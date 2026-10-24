#!/usr/bin/env python3
"""Mapeamento passivo de um produto web para o modo catálogo da aidd-tutorial-creator.

Por perfil: entra (atalho de teste, sessão do navegador do usuário ou página pública), captura a tela inicial
e explora SÓ controles de leitura (visualização, filtro, aba, ordenação) e links internos seguros.
Nunca preenche formulário nem clica em salvar/enviar/excluir/gerar/exportar/sair.

Uso:
  python explore.py <saida> --base https://app --perfil "Consultor" --entrar atalho
  python explore.py <saida> --base https://app --perfil "Minha conta" --entrar cdp --cdp http://127.0.0.1:9222 --target <id>
  python explore.py <saida> --base https://app --perfil "Formulário" --entrar publico --caminho /pre_cadastro?t=demo
Saída por perfil: <saida>/<perfil>/{entrar,explorar}.json, shots/*.png, *.a11y.txt, explorar.summary.json
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

TUTORIAL = Path(__file__).resolve().parent / "tutorial.py"
UNSAFE_URL = re.compile(r"logout|sair|signout|sign-out|delete|excluir|remov|apagar|destroy|reset|enviar|submit|send|"
                        r"aprovar|approve|reject|rejeitar|cancel|export|download|token|/api/", re.I)
SAFE_BUTTON = re.compile(r"^(Visualização em |Ver |Visualizar|Mostrar |Fila |Relatórios|Métricas|Hoje$|Ontem$|\d+D$|"
                         r"Recentes$|A-Z$|Z-A$|Todos|Ativos|Inativos|Cards$|Lista$|Kanban$|Mapa$|Tabela$|Grade$|"
                         r"Anterior$|Próxima$|Links gerados|Enviados|Em análise|Em correção|Aprovados \d|Reprovados \d)", re.I)
UNSAFE_BUTTON = re.compile(r"salvar|enviar|excluir|apagar|remover|inativar|ativar |gerar|criar|novo|nova|adicionar|"
                           r"exportar|imprimir|baixar|download|sair|logout|aprovar|reprovar|confirmar|publicar|"
                           r"reenviar|resetar|restaurar|duplicar|importar", re.I)
TABS_LAST = re.compile(r"^(Fila |Relatórios|Métricas)", re.I)


def slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def find_browser() -> str:
    cands = {
        "Windows": [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"],
        "Darwin": ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                   "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"],
    }.get(platform.system(), [])
    for c in cands + [shutil.which(n) or "" for n in ("google-chrome", "chromium", "chromium-browser", "chrome", "msedge")]:
        if c and Path(c).exists():
            return c
    sys.exit("navegador Chromium não encontrado (informe --chrome)")


def rea_command() -> list[str]:
    """REA CLI: 'rea' no PATH; senão o pacote já baixado pelo MCP no cache do npm; senão npx (baixa: peça OK)."""
    if shutil.which("rea"):
        return [shutil.which("rea")]
    cache = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".npm")) / ("npm-cache" if os.name == "nt" else "")
    for base in {cache / "_npx", Path.home() / ".npm" / "_npx"}:
        hits = sorted(glob.glob(str(base / "*" / "node_modules" / "rea-agents" / "scripts" / "rea.mjs")),
                      key=os.path.getmtime, reverse=True)
        if hits:
            return ["node", hits[0]]
    return ["npx", "-y", "rea-agents@latest"]


def run(scn: dict, out: Path, name: str) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    sf = out / f"{name}.scenario.json"
    sf.write_text(json.dumps(scn, ensure_ascii=False, indent=2), encoding="utf-8")
    cmd = rea_command() + ["capture-browser-scenario", str(sf), "--json"]
    exe = shutil.which(cmd[0]) or cmd[0]
    r = subprocess.run([exe, *cmd[1:]], capture_output=True, text=True, encoding="utf-8", timeout=1200)
    (out / f"{name}.json").write_text(r.stdout, encoding="utf-8")
    subprocess.run([sys.executable, "-I", str(TUTORIAL), "extract-rea", str(out / f"{name}.json"), str(out / "shots")],
                   capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"error": (r.stderr or "sem saída")[-800:]}


def steps_of(data) -> dict:
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
    return {s["step_id"]: s for s in found}


def a11y(step) -> str:
    return (((step or {}).get("artifacts") or {}).get("accessibility") or {}).get("value", {}).get("text", "") or ""


def controls(text: str) -> list[dict]:
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


def scenario(args, actions: list) -> dict:
    if args.entrar == "cdp":
        browser = {"mode": "connect", "cdp_endpoint": args.cdp, "target_id": args.target}
    else:
        browser = {"mode": "launch", "executable_path": args.chrome or find_browser()}
    return {"browser": browser, "start_url": {"url": args.base + (args.caminho or "")},
            "environment": {"locale": args.locale, "timezone": args.timezone,
                            "viewport": {"width": 1280, "height": 720, "device_scale_factor": 1.5}},
            "actions": actions, "capture": {"after_each_step": ["screenshot", "accessibility"], "at_end": ["url"]}}


def entry_actions(args) -> list:
    acts = [{"step_id": "inicio", "action": "wait_for_timeout", "duration_ms": 1500}]
    if args.entrar == "atalho":
        acts.append({"step_id": "atalho", "action": "click", "timeout_ms": 15000,
                     "locator": {"kind": "role", "role": args.papel_atalho, "name": args.atalho or args.perfil}})
    acts.append({"step_id": "home", "action": "wait_for_timeout", "duration_ms": args.espera})
    return acts


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("saida")
    ap.add_argument("--base", required=True, help="origem do produto, ex.: https://app.exemplo.com")
    ap.add_argument("--perfil", required=True, help="nome do perfil (vira a pasta em kebab-case)")
    ap.add_argument("--entrar", choices=["atalho", "cdp", "publico"], required=True)
    ap.add_argument("--atalho", help="rótulo do botão de atalho (padrão: o nome do perfil)")
    ap.add_argument("--papel-atalho", dest="papel_atalho", default="button", choices=["button", "link"])
    ap.add_argument("--caminho", help="caminho inicial (ex.: /pre_cadastro?t=demo)")
    ap.add_argument("--cdp", help="endpoint CDP do navegador do usuário (modo cdp)")
    ap.add_argument("--target", help="target_id da aba (modo cdp; liste com list_browser_targets)")
    ap.add_argument("--chrome")
    ap.add_argument("--espera", type=int, default=4000, help="ms de espera após entrar")
    ap.add_argument("--locale", default="pt-BR")
    ap.add_argument("--timezone", default="America/Sao_Paulo")
    args = ap.parse_args()
    base = args.base.rstrip("/")
    args.base = base
    out = Path(args.saida) / slug(args.perfil)

    # passada 1: entrar e ler a tela inicial
    first = steps_of(run(scenario(args, entry_actions(args)), out, "entrar"))
    home = first.get("home")
    ctrls = controls(a11y(home))
    home_url = ((home or {}).get("after_url") or {}).get("url")
    print(f"== {args.perfil}: {home_url} · {len(ctrls)} controles")

    # passada 2: só leitura (lista de permitidos), abas por último, links internos seguros depois
    acts, plan = entry_actions(args), [("home", "tela inicial")]
    buttons = [c["name"] for c in ctrls if c["role"] in ("button", "tab")
               and SAFE_BUTTON.search(c["name"]) and not UNSAFE_BUTTON.search(c["name"])]
    # ordem: filtros/visualizações → abas (trocam o conteúdo) → Próxima → Anterior (costuma estar desabilitado na pág. 1,
    # e o REA interrompe o cenário no primeiro clique que falha)
    order = lambda n: (3 if n == "Anterior" else 2 if n == "Próxima" else 1 if TABS_LAST.search(n) else 0)
    buttons = sorted(dict.fromkeys(buttons), key=order)
    for i, name in enumerate(buttons, 1):
        acts += [{"step_id": f"b{i:02d}", "action": "click", "timeout_ms": 8000,
                  "locator": {"kind": "role", "role": "button", "name": name}},
                 {"step_id": f"b{i:02d}-tela", "action": "wait_for_timeout", "duration_ms": 1800}]
        plan.append((f"b{i:02d}-tela", f"botão: {name}"))
    links_ok = [(c["name"], base + c["url"]) for c in ctrls if c["role"] == "link" and (c.get("url") or "").startswith("/")
                and not UNSAFE_URL.search(c["url"])]
    for j, (name, url) in enumerate(dict.fromkeys(links_ok), 1):
        acts += [{"step_id": f"l{j:02d}", "action": "goto", "destination": {"url": url}, "wait_until": "load",
                  "timeout_ms": 30000},
                 {"step_id": f"l{j:02d}-tela", "action": "wait_for_timeout", "duration_ms": 2500}]
        plan.append((f"l{j:02d}-tela", f"link: {name} ({url[len(base):]})"))
    steps = steps_of(run(scenario(args, acts), out, "explorar"))
    telas, failed = [], []
    for sid, label in plan:
        s = steps.get(sid)
        ok = bool(s) and (s.get("action_status") or s.get("status")) in (None, "completed")
        if not ok:
            failed.append(sid)
        txt = a11y(s)
        (out / f"{sid}.a11y.txt").write_text(txt, encoding="utf-8")
        telas.append({"id": sid, "o_que": label, "url": ((s or {}).get("after_url") or {}).get("url"), "capturada": ok,
                      "titulos": re.findall(r"- heading \"([^\"]+)\"", txt)[:5],
                      "screenshot": f"shots/{sid}.png" if s else None,
                      "controles": [f"{c['role']}:{c['name']}" for c in controls(txt)][:60]})
    skipped = sorted({c["name"] for c in ctrls if c["role"] in ("button", "tab") and c["name"] not in buttons})
    (out / "explorar.summary.json").write_text(json.dumps(
        {"perfil": args.perfil, "entrada": args.entrar, "tela_inicial": home_url, "telas": telas,
         "acoes_nao_executadas": skipped, "passos_com_falha": failed}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"   {len(telas) - len(failed)}/{len(telas)} telas capturadas; {len(skipped)} controles de ação listados sem clicar"
          + (f"; falhas: {failed}" if failed else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
