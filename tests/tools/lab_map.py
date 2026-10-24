"""Mapeamento passivo do laboratório por perfil (atalhos de teste da tela de login).

Fase 'entrar': clica no atalho do perfil e captura a tela inicial (screenshot + acessibilidade + URL).
Fase 'rotas': na mesma sessão, abre por endereço cada rota encontrada (GET) e captura cada tela.
Nunca preenche formulário nem clica em salvar/enviar/excluir. Rotas com cara de ação são descartadas.

Uso: python lab_map.py entrar <saida> <Perfil> [<Perfil> ...]
     python lab_map.py rotas  <saida> <Perfil>
"""
import json
import re
import subprocess
import sys
from pathlib import Path

BASE = "https://cadastros.vpsconexao.org"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
REA = r"C:\Users\trcnologia\AppData\Local\npm-cache\_npx\dea9475797100b20\node_modules\rea-agents\scripts\rea.mjs"
TUTORIAL = Path(__file__).resolve().parents[2] / "aidd-tutorial-creator" / "scripts" / "tutorial.py"
UNSAFE = re.compile(r"logout|sair|signout|sign-out|delete|excluir|remov|apagar|destroy|reset_pw|"
                    r"enviar|submit|send|aprovar|approve|reject|rejeitar|cancel|export|download|token|api/", re.I)


def slug(s: str) -> str:
    import unicodedata
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def run_scenario(scn: dict, out: Path, name: str) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    sf = out / f"{name}.scenario.json"
    sf.write_text(json.dumps(scn, ensure_ascii=False, indent=2), encoding="utf-8")
    r = subprocess.run(["node", REA, "capture-browser-scenario", str(sf), "--json"], capture_output=True, text=True,
                       encoding="utf-8", timeout=900)
    (out / f"{name}.json").write_text(r.stdout, encoding="utf-8")
    subprocess.run([sys.executable, "-I", str(TUTORIAL), "extract-rea", str(out / f"{name}.json"), str(out / "shots")],
                   capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"error": r.stderr[-800:]}


def steps_of(data) -> list[dict]:
    found = []

    def walk(n):
        if isinstance(n, dict):
            if "step_id" in n and "artifacts" in n:
                found.append(n)
            for v in n.values():
                walk(v)
        elif isinstance(n, list):
            for v in n:
                walk(v)
    walk(data)
    # o resultado repete passos em mais de um lugar; mantém o último de cada step_id
    return list({s["step_id"]: s for s in found}.values())


def a11y(step) -> str:
    return ((step.get("artifacts") or {}).get("accessibility") or {}).get("value", {}).get("text", "") or ""


def url_of(step) -> str:
    return (step.get("after_url") or {}).get("url", "")


def links(text: str) -> list[dict]:
    out, last = [], None
    for line in text.splitlines():
        m = re.match(r"\s*- (link|button|tab|menuitem) \"([^\"]+)\"", line)
        if m:
            last = {"role": m.group(1), "name": m.group(2)}
            out.append(last)
        u = re.match(r"\s*- /url: (\S+)", line)
        if u and last is not None:
            last["url"] = u.group(1)
    return out


def scenario(actions: list, capture_each=True) -> dict:
    return {
        "browser": {"mode": "launch", "executable_path": CHROME},
        "start_url": {"url": BASE},
        "environment": {"locale": "pt-BR", "timezone": "America/Sao_Paulo",
                        "viewport": {"width": 1280, "height": 720, "device_scale_factor": 1.5}},
        "actions": actions,
        "capture": {"after_each_step": ["screenshot", "accessibility"] if capture_each else [], "at_end": ["url"]},
    }


def login_actions(perfil: str) -> list:
    return [
        {"step_id": "login-page", "action": "wait_for_timeout", "duration_ms": 1500},
        {"step_id": f"atalho-{slug(perfil)}", "action": "click",
         "locator": {"kind": "role", "role": "button", "name": perfil}, "timeout_ms": 15000},
        {"step_id": f"home-{slug(perfil)}", "action": "wait_for_timeout", "duration_ms": 4000},
    ]


def fase_entrar(out: Path, perfis: list[str]) -> None:
    for perfil in perfis:
        p = slug(perfil)
        data = run_scenario(scenario(login_actions(perfil)), out / p, "entrar")
        steps = steps_of(data)
        home = next((s for s in steps if s["step_id"] == f"home-{p}"), None)
        info = {"perfil": perfil, "url": url_of(home) if home else None,
                "status": [(s["step_id"], (s.get("action_status") or s.get("status"))) for s in steps],
                "links": links(a11y(home)) if home else [], "erro": data.get("error")}
        (out / p / "home.a11y.txt").write_text(a11y(home) if home else "", encoding="utf-8")
        (out / p / "entrar.summary.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"== {perfil}: {info['url']} · {len(info['links'])} links/botões" + (f" · ERRO {info['erro'][:200]}" if info["erro"] else ""))


def fase_rotas(out: Path, perfil: str) -> None:
    p = slug(perfil)
    summ = json.loads((out / p / "entrar.summary.json").read_text(encoding="utf-8"))
    routes, skipped = [], []
    for l in summ["links"]:
        u = l.get("url")
        if not u or u.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        full = u if u.startswith("http") else BASE + (u if u.startswith("/") else "/" + u)
        if not full.startswith(BASE):
            continue
        (skipped if UNSAFE.search(full) else routes).append(full)
    routes = list(dict.fromkeys(r for r in routes if r.rstrip("/") != (summ["url"] or "").rstrip("/")))
    actions = login_actions(perfil)
    for i, r in enumerate(routes, 1):
        actions.append({"step_id": f"r{i:02d}", "action": "goto", "destination": {"url": r}, "wait_until": "load",
                        "timeout_ms": 30000})
        actions.append({"step_id": f"r{i:02d}-tela", "action": "wait_for_timeout", "duration_ms": 2500})
    data = run_scenario(scenario(actions), out / p, "rotas")
    steps = {s["step_id"]: s for s in steps_of(data)}
    telas = []
    for i, r in enumerate(routes, 1):
        s = steps.get(f"r{i:02d}-tela")
        txt = a11y(s) if s else ""
        (out / p / f"r{i:02d}.a11y.txt").write_text(txt, encoding="utf-8")
        heads = re.findall(r"- heading \"([^\"]+)\"", txt)
        telas.append({"id": f"r{i:02d}", "rota": r, "url_final": url_of(s) if s else None,
                      "titulos": heads[:4], "screenshot": f"shots/r{i:02d}-tela.png",
                      "elementos": [f"{l['role']}:{l['name']}" for l in links(txt)][:40]})
    (out / p / "rotas.summary.json").write_text(json.dumps({"perfil": perfil, "visitadas": telas, "descartadas": skipped},
                                                           ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"== {perfil}: {len(telas)} telas visitadas, {len(skipped)} rotas descartadas por segurança"
          + (f" · ERRO {data['error'][:200]}" if data.get("error") else ""))


SAFE_BUTTON = re.compile(r"^(Visualização em |Fila Operacional|Relatórios & Métricas|Hoje$|7D$|30D$|Recentes$|"
                         r"Ver pendentes$|Links gerados|Enviados|Em análise|Em correção|Aprovados \d|Reprovados \d)")


def fase_explorar(out: Path, perfil: str, wait_login_ms: int = 4000, start_path: str | None = None) -> None:
    """Clica só em controles de visualização/filtro/aba (lista de permitidos) e abre links internos seguros."""
    p = slug(perfil)
    summ = json.loads((out / p / "entrar.summary.json").read_text(encoding="utf-8"))
    if start_path:  # perfil que é uma página pública (ex.: formulário demo): só abre e observa
        actions = [{"step_id": "abrir", "action": "goto", "destination": {"url": BASE + start_path}, "wait_until": "load",
                    "timeout_ms": 30000}, {"step_id": "tela", "action": "wait_for_timeout", "duration_ms": 3000}]
        plan = [("tela", f"página {start_path}")]
    else:
        actions = login_actions(perfil)
        actions[-1]["duration_ms"] = wait_login_ms
        plan = [(actions[-1]["step_id"], "tela inicial")]
        buttons = [l["name"] for l in summ["links"] if l["role"] in ("button", "tab") and SAFE_BUTTON.search(l["name"])]
        # abas trocam o conteúdo e escondem filtros: filtros e visualizações primeiro, abas por último
        buttons.sort(key=lambda n: n.startswith(("Fila Operacional", "Relatórios & Métricas")))
        for i, name in enumerate(dict.fromkeys(buttons), 1):
            actions.append({"step_id": f"b{i:02d}", "action": "click",
                            "locator": {"kind": "role", "role": "button", "name": name}, "timeout_ms": 8000})
            actions.append({"step_id": f"b{i:02d}-tela", "action": "wait_for_timeout", "duration_ms": 1800})
            plan.append((f"b{i:02d}-tela", f"botão: {name}"))
        links_ok = []
        for l in summ["links"]:
            u = l.get("url") or ""
            if l["role"] == "link" and u.startswith("/") and not UNSAFE.search(u):
                links_ok.append((l["name"], BASE + u))
        for j, (name, url) in enumerate(dict.fromkeys(links_ok), 1):
            actions.append({"step_id": f"l{j:02d}", "action": "goto", "destination": {"url": url}, "wait_until": "load",
                            "timeout_ms": 30000})
            actions.append({"step_id": f"l{j:02d}-tela", "action": "wait_for_timeout", "duration_ms": 2500})
            plan.append((f"l{j:02d}-tela", f"link: {name} ({url[len(BASE):]})"))
    data = run_scenario(scenario(actions), out / p, "explorar")
    steps = {s["step_id"]: s for s in steps_of(data)}
    telas = []
    for sid, label in plan:
        s = steps.get(sid)
        txt = a11y(s) if s else ""
        (out / p / f"{sid}.a11y.txt").write_text(txt, encoding="utf-8")
        telas.append({"id": sid, "o_que": label, "url": url_of(s) if s else None,
                      "capturada": bool(s), "titulos": re.findall(r"- heading \"([^\"]+)\"", txt)[:5],
                      "screenshot": f"shots/{sid}.png" if s else None,
                      "controles": [f"{l['role']}:{l['name']}" for l in links(txt)][:50]})
    failed = [s["step_id"] for s in steps.values() if (s.get("action_status") or s.get("status")) not in (None, "completed")]
    (out / p / "explorar.summary.json").write_text(json.dumps({"perfil": perfil, "telas": telas, "passos_com_falha": failed},
                                                              ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"== {perfil}: {sum(t['capturada'] for t in telas)}/{len(telas)} telas capturadas"
          + (f" · falhas: {failed}" if failed else "") + (f" · ERRO {data['error'][:160]}" if data.get("error") else ""))


if __name__ == "__main__":
    fase, out = sys.argv[1], Path(sys.argv[2])
    if fase == "entrar":
        fase_entrar(out, sys.argv[3:])
    elif fase == "explorar":
        extra = sys.argv[4] if len(sys.argv) > 4 else None
        if extra and extra.startswith("/"):
            fase_explorar(out, sys.argv[3], start_path=extra)
        else:
            fase_explorar(out, sys.argv[3], wait_login_ms=int(extra or 4000))
    else:
        fase_rotas(out, sys.argv[3])
