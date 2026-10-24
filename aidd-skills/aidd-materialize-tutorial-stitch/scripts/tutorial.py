#!/usr/bin/env python3
"""Utilitários determinísticos da skill aidd-tutorial-creator.

Somente biblioteca padrão. Dependências externas são chamadas por subprocesso
quando o subcomando precisa delas (ffmpeg/ffprobe, npx hyperframes, yt-dlp,
faster-whisper). Rode `python tutorial.py <subcomando> --help`.
"""
from __future__ import annotations

import argparse
import base64
import difflib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

HOME = Path(__file__).resolve().parent.parent
TEMPLATES = HOME / "templates"

LAYOUTS = {
    "title", "app-full", "zoom-focus", "callout", "cursor-path", "split",
    "step-list", "device-frame", "pip", "result", "outro",
}
REQUIRED_SCENE_FIELDS = ("id", "start", "end", "layout", "steps", "narration", "visual")
CONTIGUITY_TOL = 0.05
DURATION_TOL = 0.5
MIN_SCENE = 1.5
MAX_TEXT_WORDS = 7
MAX_TEXT_ITEMS = 3
PNG_MAGIC_B64 = "iVBORw0KGgo"


# ---------------------------------------------------------------- ambiente & credenciais

def load_dotenv_hierarchy() -> list[Path]:
    """Carrega variáveis de arquivos .env subindo a árvore de diretórios sem dependências externas."""
    loaded = []
    search_dirs = [Path.cwd().resolve(), Path(__file__).resolve().parent, HOME, HOME.parent]
    cur = Path.cwd().resolve()
    for parent in cur.parents:
        if parent not in search_dirs:
            search_dirs.append(parent)

    candidates = [".env", ".env.local", ".env-gemini", ".env-full"]
    seen = set()
    for d in search_dirs:
        for name in candidates:
            p = d / name
            if p.is_file() and p not in seen:
                seen.add(p)
                try:
                    for line in p.read_text(encoding="utf-8-sig", errors="ignore").splitlines():
                        line = line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        if k and k not in os.environ:
                            os.environ[k] = v
                    loaded.append(p)
                except Exception:
                    pass
    return loaded

# Carrega variáveis de ambiente imediatamente no início
load_dotenv_hierarchy()


def extract_global_flags(argv: list[str]) -> list[str]:
    """Extrai flags globais de credenciais (--api-key, --gemini-api-key, --fish-api-key)."""
    clean_argv = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in ("--api-key", "--gemini-api-key"):
            if i + 1 < len(argv):
                os.environ["GEMINI_API_KEY"] = argv[i + 1]
                i += 2
                continue
        elif arg.startswith("--api-key=") or arg.startswith("--gemini-api-key="):
            os.environ["GEMINI_API_KEY"] = arg.split("=", 1)[1].strip("'\"")
            i += 1
            continue
        elif arg in ("--fish-api-key",):
            if i + 1 < len(argv):
                os.environ["FISH_API_KEY"] = argv[i + 1]
                i += 2
                continue
        elif arg.startswith("--fish-api-key="):
            os.environ["FISH_API_KEY"] = arg.split("=", 1)[1].strip("'\"")
            i += 1
            continue
        clean_argv.append(arg)
        i += 1
    return clean_argv


_POOL_INDEX = 0

def get_gemini_key_pool() -> list[str]:
    """Retorna todas as chaves Gemini disponíveis (direta ou nos slots DEV_XX_GEMINI_API_KEY)."""
    keys = []
    direct = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if direct and direct.strip() and direct.strip() not in keys:
        keys.append(direct.strip())
    # Busca chaves dos desenvolvedores (.env-gemini / slots)
    for k in sorted(os.environ.keys()):
        if "GEMINI_API_KEY" in k and k not in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
            v = os.environ[k].strip().strip("'\"")
            if v and len(v) >= 20 and v not in keys:
                keys.append(v)
    return keys


def get_gemini_key() -> str | None:
    """Retorna uma chave ativa do Gemini, priorizando a direta ou a primeira do pool de devs."""
    pool = get_gemini_key_pool()
    return pool[0] if pool else None


# ---------------------------------------------------------------- utilidades

def die(msg: str, code: int = 2) -> None:
    print(f"erro: {msg}", file=sys.stderr)
    sys.exit(code)


def which(name: str) -> str | None:
    return shutil.which(name)


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    exe = which(cmd[0]) or cmd[0]
    return subprocess.run([exe, *cmd[1:]], **kw)


def load_json(path: Path):
    try:
        # utf-8-sig: o PowerShell 5.1 grava JSON com BOM
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        die(f"arquivo não encontrado: {path}")
    except json.JSONDecodeError as e:
        die(f"JSON inválido em {path}: {e}")


def words(text: str) -> list[str]:
    return re.findall(r"[\wÀ-ÿ]+(?:[-'’][\wÀ-ÿ]+)*", text, flags=re.UNICODE)


def norm_token(tok: str) -> str:
    tok = unicodedata.normalize("NFKD", tok.lower())
    return "".join(c for c in tok if not unicodedata.combining(c))


def ffprobe(path: Path) -> dict:
    if not which("ffprobe"):
        die("ffprobe não encontrado (instale o ffmpeg)")
    out = run(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        die(f"ffprobe falhou em {path}: {out.stderr.strip()}")
    return json.loads(out.stdout)


def media_duration(path: Path) -> float:
    return float(ffprobe(path)["format"]["duration"])


# ---------------------------------------------------------------- doctor

def cmd_doctor(args) -> int:
    rows = []

    def add(name, ok, detail):
        rows.append((name, "OK " if ok else "--", detail))

    add("python", True, sys.version.split()[0])
    for tool in ("ffmpeg", "ffprobe", "node", "npx", "yt-dlp", "adb"):
        p = which(tool)
        add(tool, bool(p), p or "ausente")
    try:
        import faster_whisper  # noqa: F401
        add("faster-whisper", True, "importável")
    except Exception:
        add("faster-whisper", False, "ausente (legendas/transcrição usarão hyperframes transcribe)")
    for mod, label, hint in (("edge_tts", "voz edge (neural, grátis)", "pip install edge-tts"),
                             ("google.genai", "voz gemini (SDK)", "pip install google-genai"),
                             ("kokoro_onnx", "voz kokoro (local)", "pip install kokoro-onnx soundfile")):
        try:
            __import__(mod)
            add(label, True, "importável")
        except Exception:
            add(f"{label} (opcional)", False, hint)
    pool = get_gemini_key_pool()
    if pool:
        if len(pool) > 1:
            add("chave Gemini (pool de devs)", True, f"{len(pool)} chaves ativas do .env-gemini (com rotação automática)")
        else:
            masked = pool[0][:6] + "..." + pool[0][-4:] if len(pool[0]) > 10 else "***"
            add("chave Gemini (opcional)", True, f"definida ({masked})")
    else:
        add("chave Gemini (opcional)", False, "GEMINI_API_KEY não definida (use: tutorial set-key ou crie em aistudio.google.com)")

    fish_val = os.environ.get("FISH_API_KEY")
    add("chave Fish Audio (opcional)", bool(fish_val), "definida" if fish_val else "FISH_API_KEY não definida")
    r = run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True) if which("ffmpeg") else None
    add("ffmpeg libass (legendas queimadas)", bool(r and " subtitles " in r.stdout), "ok" if r and " subtitles " in r.stdout else "filtro subtitles ausente")
    if which("npx"):
        r = run(["npx", "--yes", "hyperframes", "--version"], capture_output=True, text=True, timeout=300)
        ver = (r.stdout.strip().splitlines() or [""])[-1]
        add("hyperframes (npx)", r.returncode == 0, ver or r.stderr.strip()[:120])
    else:
        add("hyperframes (npx)", False, "npx ausente")
    browsers = {
        "Windows": [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"],
        "Darwin": ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                   "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"],
        "Linux": ["/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser"],
    }.get(platform.system(), [])
    found = [b for b in browsers if Path(b).exists()]
    add("navegador Chromium", bool(found), found[0] if found else "nenhum caminho padrão encontrado")
    gh = os.environ.get("GHIDRA_INSTALL_DIR")
    add("Ghidra (opcional, rota N2)", bool(gh and Path(gh).exists()), gh or "GHIDRA_INSTALL_DIR não definido")
    add("REA", True, "verifique as ferramentas mcp__rea__* na harness; sem MCP: npx -y rea-agents@latest")
    width = max(len(r[0]) for r in rows)
    for name, status, detail in rows:
        print(f"[{status}] {name.ljust(width)}  {detail}")
    missing = [r[0] for r in rows if r[1] == "--" and "opcional" not in r[0] and r[0] != "adb"]
    if missing:
        print(f"\nfaltando (obrigatórios para alguma fase): {', '.join(missing)}")
    return 0


# ---------------------------------------------------------------- init

def cmd_init(args) -> int:
    root = Path(args.dir)
    if root.exists() and any(root.iterdir()) and not args.force:
        die(f"{root} já existe e não está vazio (use --force para completar arquivos ausentes)")
    for sub in ("evidence", "keyframes", "audio", "assets", "composition", "snapshots", "renders", "source"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    copies = {
        "ESTADO.md": "ESTADO.md", "rules.md": "rules.md", "step-map.json": "step-map.json",
        "storyboard.json": "storyboard.json", "browser-scenario.json": "evidence/browser-scenario.json",
    }
    for src, dst in copies.items():
        target = root / dst
        if target.exists():
            continue
        text = (TEMPLATES / src).read_text(encoding="utf-8").replace("<slug>", root.name)
        target.write_text(text, encoding="utf-8")
    for name, body in (("brief.md", "# Brief\n"), ("script.md", "# Roteiro\n\nDireção: \n"),
                       ("blueprint.md", "# Blueprint\n")):
        if not (root / name).exists():
            (root / name).write_text(body, encoding="utf-8")
    cfg_path = root / "tutorial.config.json"
    cfg = load_json(cfg_path) if cfg_path.exists() else {}
    cfg = merge_config(cfg, flags_to_config(args))
    cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    registrar(root, f"projeto criado · {describe_config(cfg)}")
    print(f"projeto pronto em {root.resolve()}")
    print(describe_config(cfg))
    return 0


FORMATS = {"16:9": (1920, 1080), "9:16": (1080, 1920), "1:1": (1080, 1080), "4:5": (1080, 1350)}
RESOLUTIONS = {"480p": 480, "720p": 720, "1080p": 1080}
# Onde o vídeo vai ser usado → saídas, legenda, zonas seguras (fração da altura coberta pela interface do app/rede),
# loudness e limites. Valores de partida; o usuário pode sobrescrever qualquer um por flag.
CHANNELS = {
    "instagram-reels": {"rotulo": "Instagram Reels", "saidas": [("9:16", "1080p")], "legenda": "bold-pop", "tamanho": "g",
                        "seguro_topo": 0.14, "seguro_base": 0.22, "lufs": -14, "max_s": 90},
    "instagram-feed": {"rotulo": "Instagram feed", "saidas": [("4:5", "1080p")], "legenda": "highlight", "tamanho": "m",
                       "seguro_topo": 0.05, "seguro_base": 0.10, "lufs": -14, "max_s": 60},
    "tiktok": {"rotulo": "TikTok", "saidas": [("9:16", "1080p")], "legenda": "bold-pop", "tamanho": "g",
               "seguro_topo": 0.12, "seguro_base": 0.25, "lufs": -14, "max_s": 180},
    "youtube-shorts": {"rotulo": "YouTube Shorts", "saidas": [("9:16", "1080p")], "legenda": "bold-pop", "tamanho": "g",
                       "seguro_topo": 0.10, "seguro_base": 0.20, "lufs": -14, "max_s": 180},
    "youtube": {"rotulo": "YouTube", "saidas": [("16:9", "1080p")], "legenda": "highlight", "tamanho": "m",
                "seguro_topo": 0.0, "seguro_base": 0.08, "lufs": -14, "max_s": None},
    "plataforma-ensino": {"rotulo": "Plataforma de ensino / EAD", "saidas": [("16:9", "1080p"), ("16:9", "720p")],
                          "legenda": "boxed", "tamanho": "m", "seguro_topo": 0.0, "seguro_base": 0.10, "lufs": -16,
                          "max_s": None},
    "central-de-ajuda": {"rotulo": "Central de ajuda / docs do produto", "saidas": [("16:9", "1080p"), ("16:9", "720p")],
                         "legenda": "clean", "tamanho": "m", "seguro_topo": 0.0, "seguro_base": 0.08, "lufs": -16,
                         "max_s": None},
    "linkedin": {"rotulo": "LinkedIn feed", "saidas": [("1:1", "1080p")], "legenda": "highlight", "tamanho": "m",
                 "seguro_topo": 0.0, "seguro_base": 0.10, "lufs": -14, "max_s": 600},
    "whatsapp": {"rotulo": "WhatsApp", "saidas": [("9:16", "720p")], "legenda": "bold-pop", "tamanho": "g",
                 "seguro_topo": 0.0, "seguro_base": 0.12, "lufs": -14, "max_s": 180, "maxrate": "2M"},
    "apresentacao": {"rotulo": "Apresentação / reunião", "saidas": [("16:9", "1080p")], "legenda": "none", "tamanho": "m",
                     "seguro_topo": 0.0, "seguro_base": 0.08, "lufs": -16, "max_s": None},
}


# Viewport de captura por formato quando o app é responsivo (a tela do vídeo nasce no tamanho certo)
CAPTURE_VIEWPORTS = {
    "16:9": {"width": 1280, "height": 720, "dsf": 1.5, "mobile": False},
    "9:16": {"width": 390, "height": 844, "dsf": 3, "mobile": True},
    "1:1": {"width": 820, "height": 820, "dsf": 2, "mobile": False},
    "4:5": {"width": 768, "height": 960, "dsf": 2, "mobile": False},
}


def find_playwright() -> Path | None:
    """playwright-core: o que veio com o REA (cache do npx) ou instalação global."""
    cands = []
    local = Path(os.environ.get("LOCALAPPDATA", "")) / "npm-cache" / "_npx"
    for base in (local, Path.home() / ".npm" / "_npx"):
        cands += sorted(base.glob("*/node_modules/playwright-core/package.json"), key=os.path.getmtime, reverse=True)
    r = run(["npm", "root", "-g"], capture_output=True, text=True) if which("npm") else None
    if r and r.returncode == 0:
        cands.append(Path(r.stdout.strip()) / "playwright-core" / "package.json")
    return next((c for c in cands if c.exists()), None)


def chrome_path() -> str | None:
    for c in (r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
              "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "/usr/bin/google-chrome", "/usr/bin/chromium"):
        if Path(c).exists():
            return c
    return None


def cmd_responsive(args) -> int:
    pw = find_playwright() or die("playwright-core não encontrado (vem com o REA; ou: npm i -g playwright-core, peça OK)")
    chrome = args.chrome or chrome_path() or die("Chrome/Edge não encontrado (informe --chrome)")
    fmts = parse_list(args.formatos, FORMATS) or ["9:16"]
    out = Path(args.out)
    conf = {"url": args.url, "chrome": chrome, "playwright_from": str(pw), "out": str(out), "locale": "pt-BR",
            "viewports": [{"formato": f, **CAPTURE_VIEWPORTS[f]} for f in fmts],
            "paths": [p.strip() for p in (args.caminhos or "").split(",") if p.strip()],
            "login": {"role": args.papel_atalho, "name": args.atalho, "wait_ms": 4000} if args.atalho else None}
    out.mkdir(parents=True, exist_ok=True)
    cf = out / "responsive.config.json"
    cf.write_text(json.dumps(conf, ensure_ascii=False, indent=2), encoding="utf-8")
    r = run(["node", str(Path(__file__).with_name("responsive.mjs")), str(cf)], capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        die(f"medidor falhou: {r.stderr[-600:]}")
    data = load_json(out / "responsive.json")
    for res in data["resultados"]:
        rotulo = {"sim": "RESPONSIVO", "parcial": "PARCIAL (conteúdo cortado em contêiner com rolagem)", "nao": "não responsivo"}
        print(f"{res['formato']:>5} {res['viewport']:<14} → {rotulo[res.get('nivel', 'nao')]}")
        for p in res["paginas"]:
            if "erro" in p:
                print(f"      erro: {p['erro']}")
                continue
            print(f"      {p['caminho']:<28} {p.get('nivel', ''):<8} meta={'ok' if p['meta_viewport'] else 'ausente'}"
                  f" rolagem-h={p['horizontal_scroll']} vazando={p['overflowing_elements']}"
                  f" cortado-em-rolagem={p.get('clipped_in_scrollers', 0)} menor-texto={p['min_font_px']}px"
                  f" minúsculos={p['tiny_text_share']:.0%}")
    if args.projeto:
        proj = Path(args.projeto)
        cfg_path = proj / "tutorial.config.json"
        cfg = load_json(cfg_path) if cfg_path.exists() else merge_config({}, {})
        cfg.setdefault("responsivo", {})["teste"] = {r["formato"]: r.get("nivel", "nao") for r in data["resultados"]}
        cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
        registrar(proj, "teste de responsividade de " + args.url + ": "
                  + ", ".join(f"{r['formato']} {r.get('nivel', 'nao')}" for r in data["resultados"])
                  + f" (modo {cfg['responsivo'].get('modo', 'auto')})")
    return 0


def capture_plan(cfg: dict, fmt: str) -> str:
    """Como capturar as telas para um formato: 'nativa' (viewport do formato) ou 'desktop' (reenquadrar)."""
    modo = cfg.get("responsivo", {}).get("modo", "auto")
    if fmt == "16:9" or modo == "nao":
        return "desktop"
    if modo == "sim":
        return "nativa"
    # "sim" e "parcial" capturam nativo; em "parcial" o agente revisa as telas com conteúdo cortado
    return "nativa" if cfg.get("responsivo", {}).get("teste", {}).get(fmt) in ("sim", "parcial", True) else "desktop"


def output_dims(fmt: str, res: str) -> tuple[int, int]:
    """Lado menor = resolução (480/720/1080); o outro lado segue a proporção, arredondado para par."""
    fw, fh = FORMATS[fmt]
    short = RESOLUTIONS[res]
    k = short / min(fw, fh)
    return int(round(fw * k / 2) * 2), int(round(fh * k / 2) * 2)


def parse_list(v: str | None, allowed) -> list[str]:
    if not v:
        return []
    items = [x.strip() for x in v.split(",") if x.strip()]
    bad = [x for x in items if x not in allowed]
    if bad:
        die(f"valor(es) inválido(s): {bad}; use: {', '.join(allowed)}")
    return items


def registrar(proj: Path, texto: str) -> None:
    """Registra decisões e saídas em ESTADO.md (seção 'Registro de decisões'), com data."""
    import datetime
    f = proj / "ESTADO.md"
    body = f.read_text(encoding="utf-8") if f.exists() else "# Estado do tutorial\n"
    if "## Registro de decisões" not in body:
        body = body.rstrip() + "\n\n## Registro de decisões\n"
    linha = f"- {datetime.date.today().isoformat()} · {texto}"
    if linha in body.splitlines():   # o mesmo registro no mesmo dia não se repete (rodar de novo não polui)
        return
    body = body.rstrip() + f"\n{linha}\n"
    f.write_text(body, encoding="utf-8")
DEFAULT_CONFIG = {
    "format": "16:9", "width": 1920, "height": 1080, "fps": 30, "duration": None, "language": "pt-BR",
    "style": "clean-product",
    "voice": {"engine": "auto", "voice": None, "speed": 1.0, "lang": "pt-br", "direction": ""},
    "captions": {"style": None, "case": "normal", "font": "Segoe UI", "accent": "#FFD43B", "position": "auto",
                 "size": "m", "srt": True},
    "music": {"file": None, "gain_db": -20},
    "sfx": True,
    "quality": "final",
    "gates": "todos",
    "canais": [],
    "saidas": [],   # [{"formato": "9:16", "resolucao": "1080p", "canal": "instagram-reels", "legenda": "bold-pop", ...}]
}


def merge_config(base: dict, over: dict) -> dict:
    out = json.loads(json.dumps(DEFAULT_CONFIG))
    for src in (base, over):
        for k, v in src.items():
            if isinstance(v, dict):
                out.setdefault(k, {}).update({a: b for a, b in v.items() if b is not None})
            elif v is not None:
                out[k] = v
    if out["captions"].get("style") is None:
        out["captions"]["style"] = "bold-pop" if out["height"] > out["width"] else "highlight"
    return out


def flags_to_config(a) -> dict:
    cfg: dict = {"voice": {}, "captions": {}, "music": {}}
    if getattr(a, "voz", None):
        eng, _, voice = a.voz.partition(":")
        eng = {"nenhuma": "none", "sistema": "system", "google": "gemini"}.get(eng, eng)
        cfg["voice"].update(engine=eng, voice=voice or None)
    if getattr(a, "velocidade", None):
        cfg["voice"]["speed"] = a.velocidade
    if getattr(a, "direcao", None):
        cfg["voice"]["direction"] = a.direcao
    if getattr(a, "legenda", None):
        cfg["captions"]["style"] = "none" if a.legenda == "nenhuma" else a.legenda
    if getattr(a, "caixa", None):
        cfg["captions"]["case"] = {"alta": "upper", "baixa": "lower"}.get(a.caixa, a.caixa)
    if getattr(a, "legenda_posicao", None):
        cfg["captions"]["position"] = {"auto": "auto", "base": "bottom", "meio": "middle", "topo": "top"}[a.legenda_posicao]
    if getattr(a, "legenda_tamanho", None):
        cfg["captions"]["size"] = a.legenda_tamanho
    if getattr(a, "acento", None):
        cfg["captions"]["accent"] = a.acento
    if getattr(a, "formato", None):
        cfg["format"] = a.formato
        cfg["width"], cfg["height"] = FORMATS[a.formato]
    for flag, key in (("fps", "fps"), ("duracao", "duration"), ("estilo", "style"), ("idioma", "language"),
                      ("qualidade", "quality"), ("gates", "gates")):
        if getattr(a, flag, None) is not None:
            cfg[key] = getattr(a, flag)
    if getattr(a, "idioma", None):
        cfg["voice"]["lang"] = a.idioma.lower()
    if getattr(a, "idiomas", None):
        cfg["idiomas"] = [norm_idioma(x) for x in a.idiomas.split(",") if x.strip()]
    if getattr(a, "musica", None):
        cfg["music"]["file"] = None if a.musica == "nenhuma" else a.musica
    if getattr(a, "sfx", None):
        cfg["sfx"] = a.sfx == "on"
    if getattr(a, "responsivo", None):
        cfg["responsivo"] = {"modo": a.responsivo}
    saidas = []
    for canal in parse_list(getattr(a, "canal", None), CHANNELS):
        pr = CHANNELS[canal]
        cfg.setdefault("canais", []).append(canal)
        for fmt, res in pr["saidas"]:
            saidas.append({"formato": fmt, "resolucao": res, "canal": canal, "legenda": pr["legenda"],
                           "tamanho": pr["tamanho"], "seguro_topo": pr["seguro_topo"], "seguro_base": pr["seguro_base"],
                           "lufs": pr["lufs"], "max_s": pr["max_s"], "maxrate": pr.get("maxrate")})
    fmts = parse_list(getattr(a, "formatos", None), FORMATS)
    ress = parse_list(getattr(a, "resolucoes", None), RESOLUTIONS)
    if fmts or ress:
        for fmt in fmts or [cfg.get("format") or "16:9"]:
            for res in ress or ["1080p"]:
                saidas.append({"formato": fmt, "resolucao": res})
    if saidas:
        cfg["saidas"] = dedupe_outputs(saidas)
        if not getattr(a, "formato", None):  # o mestre nasce no formato da 1ª saída (composição nativa)
            cfg["format"] = saidas[0]["formato"]
            cfg["width"], cfg["height"] = FORMATS[cfg["format"]]
    return cfg


def dedupe_outputs(saidas: list[dict]) -> list[dict]:
    """Uma saída por (formato, resolução) — é o mesmo arquivo. A versão com canal (legenda, zonas seguras,
    loudness) prevalece sobre um pedido genérico do mesmo formato/resolução."""
    out: dict[tuple, dict] = {}
    for s in saidas:
        k = (s["formato"], s["resolucao"])
        if k not in out or (s.get("canal") and not out[k].get("canal")):
            out[k] = s
    return list(out.values())


def describe_config(c: dict) -> str:
    v, cap = c["voice"], c["captions"]
    dur = f", {c['duration']} s" if c.get("duration") else ""
    return (f"config: {c['format']} {c['width']}x{c['height']} {c['fps']} fps{dur}"
            f" | estilo {c['style']} | voz {v['engine']}{':' + v['voice'] if v.get('voice') else ''} x{v['speed']}"
            f" | legenda {cap['style']} ({cap['case']}, {cap.get('position', 'auto')}, tamanho {cap.get('size', 'm')},"
            f" acento {cap['accent']})"
            f" | música {c['music']['file'] or 'nenhuma'} | sfx {'on' if c['sfx'] else 'off'}"
            f" | qualidade {c['quality']} | gates {c['gates']}"
            + (f" | canais {', '.join(c['canais'])}" if c.get("canais") else "")
            + (" | saídas " + ", ".join(f"{s['formato']} {s['resolucao']}" for s in c["saidas"]) if c.get("saidas") else ""))


def add_flag_args(s) -> None:
    s.add_argument("--voz", help="motor[:voz] — edge[:pt-BR-FranciscaNeural] | gemini[:Kore] | fish[:<reference_id>] | "
                                 "kokoro[:pf_dora] | sistema | nenhuma | gravacao")
    s.add_argument("--velocidade", type=float, help="multiplicador da fala (padrão 1.0)")
    s.add_argument("--direcao", help="direção de leitura (Gemini): 'caloroso, confiante, ritmo médio'")
    s.add_argument("--legenda", choices=[*CAPTION_STYLES, "nenhuma"])
    s.add_argument("--caixa", choices=["normal", "alta", "baixa"])
    s.add_argument("--legenda-posicao", dest="legenda_posicao", choices=["auto", "base", "meio", "topo"],
                   help="auto (padrão): cada bloco vai para base/topo/meio longe do foco do passo")
    s.add_argument("--legenda-tamanho", dest="legenda_tamanho", choices=["p", "m", "g"])
    s.add_argument("--acento", help="cor de destaque da legenda (hex)")
    s.add_argument("--formato", choices=list(FORMATS))
    s.add_argument("--fps", type=int, choices=[24, 25, 30, 50, 60])
    s.add_argument("--duracao", type=float, help="duração alvo em segundos")
    s.add_argument("--estilo", choices=["clean-product", "glass-3d", "clay-soft", "paper-editorial", "dark-tech"])
    s.add_argument("--idioma", help="pt-BR, en-US, es-ES…")
    s.add_argument("--idiomas", help="idiomas de narração e legenda na vitrine (vírgulas; padrão pt-BR,en-US,es; "
                                     "um só = sem seletor)")
    s.add_argument("--musica", help="caminho de trilha local ou 'nenhuma'")
    s.add_argument("--sfx", choices=["on", "off"])
    s.add_argument("--qualidade", choices=["rascunho", "final"])
    s.add_argument("--gates", choices=["todos", "essenciais", "nenhum"])
    s.add_argument("--canal", help="onde o vídeo será usado (vírgulas): " + ", ".join(CHANNELS))
    s.add_argument("--formatos", help="saídas por proporção (vírgulas): 16:9,9:16,1:1,4:5")
    s.add_argument("--resolucoes", help="saídas por resolução (vírgulas): 480p,720p,1080p")
    s.add_argument("--responsivo", choices=["auto", "sim", "nao"],
                   help="captura nativa no tamanho de tela do formato: auto (testa), sim, nao (reenquadra o desktop)")


def cmd_config(args) -> int:
    root = Path(args.dir)
    cfg_path = root / "tutorial.config.json"
    over = flags_to_config(args)
    cfg = merge_config(load_json(cfg_path) if cfg_path.exists() else {}, over)
    cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    changed = {k: v for k, v in vars(args).items() if k not in ("dir", "fn", "cmd") and v is not None}
    if changed:
        registrar(root, "config alterado (" + ", ".join(f"--{k.replace('_', '-')} {v}" for k, v in changed.items())
                  + f") · {describe_config(cfg)}")
    print(describe_config(cfg))
    return 0


# ---------------------------------------------------------------- roteiro

SCENE_HEAD = re.compile(r"^##\s+(?P<id>[A-Za-z0-9_-]+)\s*(?:[—–-]\s*(?P<title>.*?))?\s*(?:\[steps:\s*(?P<steps>[^\]]*)\])?\s*$")


def parse_script(path: Path) -> list[dict]:
    scenes: list[dict] = []
    cur = None
    in_comment = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if in_comment:
            if "-->" in line:
                in_comment = False
            continue
        if line.startswith("<!--"):
            in_comment = "-->" not in line
            continue
        m = SCENE_HEAD.match(line)
        if m:
            cur = {
                "id": m.group("id"),
                "title": (m.group("title") or "").strip(),
                "steps": [s.strip() for s in (m.group("steps") or "").split(",") if s.strip()],
                "lines": [],
            }
            scenes.append(cur)
            continue
        if cur is None or not line or line.startswith(">") or line.startswith("#"):
            continue
        cur["lines"].append(line)
    for s in scenes:
        s["narration"] = " ".join(s.pop("lines"))
        s["words"] = len(words(s["narration"]))
    return scenes


def cmd_timing(args) -> int:
    scenes = parse_script(Path(args.script))
    if not scenes:
        die("nenhuma cena encontrada (use cabeçalhos '## c01 — Título')")
    total = 0.0
    print(f"{'cena':<8}{'palavras':>9}{'fala (s)':>10}{'+respiro':>10}")
    for s in scenes:
        speech = s["words"] / args.wps
        slot = speech + args.gap if s["words"] else args.silent
        total += slot
        print(f"{s['id']:<8}{s['words']:>9}{speech:>10.1f}{slot:>10.1f}")
    print(f"{'total':<8}{sum(s['words'] for s in scenes):>9}{'':>10}{total:>10.1f}")
    if args.target:
        diff = (total - args.target) / args.target * 100
        verdict = "OK" if abs(diff) <= 10 else ("LONGO" if diff > 0 else "CURTO")
        print(f"alvo {args.target:.1f} s → {diff:+.0f} % ({verdict})")
        return 0 if verdict == "OK" else 1
    return 0


def tts_hyperframes(txt: Path, wav: Path, voice: str | None, lang: str | None, speed: float) -> str | None:
    """Kokoro local via hyperframes. Devolve None em sucesso ou a mensagem de erro."""
    if not which("npx"):
        return "npx ausente"
    cmd = ["npx", "--yes", "hyperframes", "tts", str(txt), "-o", str(wav), "--speed", str(speed)]
    if voice:
        cmd += ["--voice", voice]
    if lang:
        cmd += ["--lang", lang]
    r = run(cmd, capture_output=True, text=True)
    if r.returncode == 0 and wav.exists():
        return None
    msg = (r.stdout + r.stderr)
    hint = re.search(r"Speech synthesis failed:[^\n]*", msg)
    return hint.group(0) if hint else msg[-400:]


def tts_system(txt: Path, wav: Path, voice: str | None, lang: str | None, speed: float) -> str | None:
    """Voz nativa do SO, sem instalação: SAPI (Windows), say (macOS), espeak-ng (Linux)."""
    system = platform.system()
    culture = {"pt-br": "pt-BR", "pt": "pt-BR", "en-us": "en-US", "en": "en-US", "es": "es-ES"}.get((lang or "pt-br").lower(), lang)
    if system == "Windows":
        rate = max(-10, min(10, round((speed - 1.0) * 10)))
        ps = (
            "Add-Type -AssemblyName System.Speech;"
            "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer;"
            "$v = $s.GetInstalledVoices() | Where-Object { $_.Enabled -and "
            "($_.VoiceInfo.Name -eq $env:TC_VOICE -or $_.VoiceInfo.Culture.Name -eq $env:TC_CULTURE) } | Select-Object -First 1;"
            "if ($v) { $s.SelectVoice($v.VoiceInfo.Name) } else { exit 3 };"
            "$s.Rate = [int]$env:TC_RATE;"
            "$s.SetOutputToWaveFile($env:TC_WAV);"
            "$s.Speak([IO.File]::ReadAllText($env:TC_TXT, [Text.Encoding]::UTF8));"
            "$s.Dispose()"
        )
        env = {**os.environ, "TC_VOICE": voice or "", "TC_CULTURE": culture or "", "TC_RATE": str(rate),
               "TC_WAV": str(wav), "TC_TXT": str(txt)}
        r = run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps], capture_output=True, text=True, env=env)
        if r.returncode == 3:
            return f"nenhuma voz SAPI para '{voice or culture}' (Configurações > Hora e idioma > Fala)"
    elif system == "Darwin":
        aiff = wav.with_suffix(".aiff")
        cmd = ["say", "-o", str(aiff), "-f", str(txt), "-r", str(int(180 * speed))]
        if voice:
            cmd += ["-v", voice]
        r = run(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            r = run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(aiff), str(wav)], capture_output=True, text=True)
            aiff.unlink(missing_ok=True)
    else:
        if not which("espeak-ng"):
            return "espeak-ng ausente"
        r = run(["espeak-ng", "-v", voice or (lang or "pt-br"), "-s", str(int(165 * speed)), "-w", str(wav), "-f", str(txt)],
                capture_output=True, text=True)
    if r.returncode != 0 or not wav.exists():
        return (r.stderr or r.stdout)[-400:]
    return None


def to_wav(src: Path, wav: Path) -> str | None:
    r = run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-ar", "48000", "-ac", "1", str(wav)],
            capture_output=True, text=True)
    return None if r.returncode == 0 and wav.exists() else r.stderr[-400:]


def tts_edge(txt: Path, wav: Path, voice: str | None, lang: str | None, speed: float, **_) -> tuple[str | None, list | None]:
    """Vozes neurais da Microsoft (edge-tts): grátis, sem chave, com tempo exato de cada palavra.
    Envia o texto da narração ao serviço online da Microsoft."""
    try:
        import asyncio
        import edge_tts
    except Exception:
        return "edge-tts ausente (pip install edge-tts: peça OK)", None
    voice = voice or {"pt-br": "pt-BR-FranciscaNeural", "en-us": "en-US-AvaMultilingualNeural",
                      "es": "es-ES-ElviraNeural"}.get((lang or "pt-br").lower(), "pt-BR-FranciscaNeural")
    rate = f"{round((speed - 1.0) * 100):+d}%"
    mp3 = wav.with_suffix(".mp3")
    words_out: list[dict] = []

    async def go():
        com = edge_tts.Communicate(txt.read_text(encoding="utf-8"), voice, rate=rate, boundary="WordBoundary")
        with open(mp3, "wb") as f:
            async for chunk in com.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    start = chunk["offset"] / 1e7
                    words_out.append({"text": chunk["text"], "start": round(start, 3),
                                      "end": round(start + chunk["duration"] / 1e7, 3)})
    try:
        asyncio.run(go())
    except Exception as e:
        return f"edge-tts falhou: {e}", None
    err = to_wav(mp3, wav)
    mp3.unlink(missing_ok=True)
    return err, restore_punctuation(words_out, txt.read_text(encoding="utf-8")) or None


def _letters(s: str) -> str:
    return "".join(c for c in norm_token(s) if c.isalnum())


def restore_punctuation(ws: list[dict], text: str) -> list[dict]:
    """O edge-tts devolve palavras sem pontuação; recupera a grafia do roteiro (vírgulas, pontos, aspas)
    casando os tokens em ordem. Uma palavra do TTS pode cobrir vários tokens ('30 dias')."""
    tokens, i = text.split(), 0
    for w in ws:
        target, taken = _letters(w["text"]), []
        while i < len(tokens) and len(_letters(" ".join(taken))) < len(target):
            taken.append(tokens[i])
            i += 1
        if taken and _letters(" ".join(taken)) == target:
            w["text"] = " ".join(taken)
            w["tok_end"] = i - 1
    return ws


BREAK_MARK = "|"


def split_breaks(text: str) -> tuple[str, set[int]]:
    """Remove o marcador de quebra de legenda '|' do texto falado e devolve os índices dos tokens
    depois dos quais a legenda deve quebrar."""
    clean, breaks = [], set()
    for tok in text.replace(BREAK_MARK, f" {BREAK_MARK} ").split():
        if tok == BREAK_MARK:
            if clean:
                breaks.add(len(clean) - 1)
        else:
            clean.append(tok)
    return " ".join(clean), breaks


def mark_breaks(ws: list[dict], breaks: set[int]) -> list[dict]:
    for w in ws:
        if w.pop("tok_end", None) in breaks:
            w["brk"] = True
    return ws


def tts_gemini(txt: Path, wav: Path, voice: str | None, lang: str | None, speed: float,
               direction: str = "", model: str | None = None, **_) -> tuple[str | None, list | None]:
    """Gemini TTS do Google AI Studio com suporte a rotação automática do pool de chaves de devs."""
    pool = get_gemini_key_pool()
    if not pool and sys.stdin.isatty():
        print("\n[Voz Gemini] Nenhuma chave GEMINI_API_KEY encontrada no ambiente ou .env-gemini.")
        try:
            k = input("Cole sua chave do Google AI Studio agora (ou Enter para cancelar): ").strip()
            if k:
                os.environ["GEMINI_API_KEY"] = k
                pool = [k]
                workspace_env = (HOME.parent if HOME.name == "aidd-materialize-tutorial-stitch" else HOME) / ".env"
                try:
                    cur_env = workspace_env.read_text(encoding="utf-8-sig") if workspace_env.exists() else ""
                    if "GEMINI_API_KEY=" in cur_env:
                        cur_env = re.sub(r"GEMINI_API_KEY=.*", f"GEMINI_API_KEY={k}", cur_env)
                    else:
                        cur_env += f"\nGEMINI_API_KEY={k}\n"
                    workspace_env.write_text(cur_env.strip() + "\n", encoding="utf-8")
                    print(f"Chave registrada em {workspace_env}")
                except Exception:
                    pass
        except Exception:
            pass
    if not pool:
        return "GEMINI_API_KEY ausente (use 'tutorial set-key' ou configure em .env / aistudio.google.com)", None
    try:
        import wave
        from google import genai
        from google.genai import types
    except Exception:
        return "google-genai ausente (pip install google-genai: peça OK)", None
    model = model or os.environ.get("TC_GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts")
    text = txt.read_text(encoding="utf-8")
    pace = "" if abs(speed - 1.0) < 0.05 else (" Leia um pouco mais rápido." if speed > 1 else " Leia um pouco mais devagar.")
    prompt = f"{direction.strip() or 'Leia em português do Brasil, tom caloroso e confiante, ritmo natural.'}{pace}\n\n{text}"

    pcm = None
    last_err = None
    for key in pool:
        try:
            client = genai.Client(api_key=key)
            resp = client.models.generate_content(
                model=model, contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice or "Kore")))))
            pcm = resp.candidates[0].content.parts[0].inline_data.data
            break
        except Exception as e:
            last_err = e
            err_str = str(e).lower()
            if any(term in err_str for term in ("429", "quota", "rate", "exhausted")):
                if len(pool) > 1:
                    continue
            break

    if not pcm:
        return f"Gemini TTS falhou ({model}): {last_err}", None
    raw = wav.with_suffix(".gemini.wav")
    with wave.open(str(raw), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(24000)
        w.writeframes(pcm)
    err = to_wav(raw, wav)
    raw.unlink(missing_ok=True)
    return err, None


def tts_fish(txt: Path, wav: Path, voice: str | None, lang: str | None, speed: float, **_) -> tuple[str | None, list | None]:
    """Fish Audio (fish.audio): vozes da comunidade e clonagem; requer FISH_API_KEY (plano grátis limitado).
    voice = reference_id do modelo de voz escolhido no site."""
    key = os.environ.get("FISH_API_KEY")
    if not key:
        return "FISH_API_KEY ausente (fish.audio > API keys)", None
    import urllib.request
    body = {"text": txt.read_text(encoding="utf-8"), "format": "mp3", "prosody": {"speed": speed}}
    if voice:
        body["reference_id"] = voice
    req = urllib.request.Request("https://api.fish.audio/v1/tts", data=json.dumps(body).encode("utf-8"),
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                                          "model": os.environ.get("TC_FISH_MODEL", "s1")})
    mp3 = wav.with_suffix(".mp3")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            mp3.write_bytes(r.read())
    except Exception as e:
        return f"Fish Audio falhou: {e}", None
    err = to_wav(mp3, wav)
    mp3.unlink(missing_ok=True)
    return err, None


def _wrap(fn):
    def call(txt, wav, voice, lang, speed, **kw):
        return fn(txt, wav, voice, lang, speed), None
    return call


TTS_ENGINES = {
    "edge": tts_edge,
    "gemini": tts_gemini,
    "fish": tts_fish,
    "kokoro": _wrap(tts_hyperframes),
    "system": _wrap(tts_system),
}
TTS_FALLBACK = ["edge", "gemini", "kokoro", "system"]


def align_words(wav: Path, text: str, lang: str | None) -> list[dict] | None:
    """Tempos por palavra via Whisper local, com a grafia do roteiro quando o número de palavras bate."""
    try:
        from faster_whisper import WhisperModel
    except Exception:
        return None
    m = WhisperModel("small", device="cpu", compute_type="int8")
    segs, _ = m.transcribe(str(wav), language=(lang or "pt")[:2], word_timestamps=True)
    heard = [{"text": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)}
             for s in segs for w in (s.words or [])]
    script_words = text.split()
    if heard and len(heard) == len(script_words):
        for idx, (h, s) in enumerate(zip(heard, script_words)):
            h["text"] = s
            h["tok_end"] = idx
    return heard or None


# Vozes prontas do Gemini TTS (lista oficial do Google AI Studio) com o caráter de cada uma; todas falam pt-BR.
GEMINI_VOICES = {
    "Zephyr": "brilhante", "Puck": "animada", "Charon": "informativa", "Kore": "firme", "Fenrir": "empolgada",
    "Leda": "jovial", "Orus": "firme", "Aoede": "leve", "Callirrhoe": "tranquila", "Autonoe": "brilhante",
    "Enceladus": "sussurrada", "Iapetus": "clara", "Umbriel": "tranquila", "Algieba": "suave", "Despina": "suave",
    "Erinome": "clara", "Algenib": "rouca", "Rasalgethi": "informativa", "Laomedeia": "animada", "Achernar": "macia",
    "Alnilam": "firme", "Schedar": "equilibrada", "Gacrux": "madura", "Pulcherrima": "assertiva", "Achird": "amigável",
    "Zubenelgenubi": "casual", "Vindemiatrix": "gentil", "Sadachbia": "vivaz", "Sadaltager": "conhecedora",
    "Sulafat": "calorosa",
}


def list_voices(engine: str, lang: str) -> list[dict]:
    """Vozes disponíveis por motor: [{engine, voice, genero, carater, idioma}]."""
    lang = lang or "pt-BR"
    out: list[dict] = []
    if engine == "edge":
        try:
            import asyncio
            import edge_tts
            vs = asyncio.run(edge_tts.list_voices())
        except Exception as e:
            print(f"aviso: edge-tts indisponível ({e})", file=sys.stderr)
            return []
        for v in vs:
            native = v["Locale"].lower() == lang.lower()
            multi = "Multilingual" in v["ShortName"]
            if native or multi:
                tags = ", ".join(v.get("VoiceTag", {}).get("VoicePersonalities", []))
                out.append({"engine": "edge", "voice": v["ShortName"], "genero": {"Female": "feminina", "Male": "masculina"}.get(v["Gender"], v["Gender"]),
                            "carater": tags.lower(), "idioma": v["Locale"] + ("" if native else " (multilíngue, com sotaque)")})
        out.sort(key=lambda x: ("multilíngue" in x["idioma"], x["voice"]))
    elif engine == "gemini":
        out = [{"engine": "gemini", "voice": k, "genero": "—", "carater": v, "idioma": "multilíngue (inclui pt-BR)"}
               for k, v in GEMINI_VOICES.items()]
    elif engine == "system" and platform.system() == "Windows":
        r = run(["powershell", "-NoProfile", "-Command",
                 "Add-Type -AssemblyName System.Speech;(New-Object System.Speech.Synthesis.SpeechSynthesizer).GetInstalledVoices()"
                 "|%{$_.VoiceInfo.Name+'|'+$_.VoiceInfo.Culture+'|'+$_.VoiceInfo.Gender}"], capture_output=True, text=True)
        for line in r.stdout.splitlines():
            n, c, g = (line.split("|") + ["", ""])[:3]
            if n:
                out.append({"engine": "system", "voice": n, "genero": {"Female": "feminina", "Male": "masculina"}.get(g, g),
                            "carater": "robótica (último recurso)", "idioma": c})
    elif engine == "kokoro":
        r = run(["npx", "--yes", "hyperframes", "tts", "--list"], capture_output=True, text=True)
        for m in re.finditer(r"\b([a-z]{2}_[a-z]+)\b", r.stdout):
            out.append({"engine": "kokoro", "voice": m.group(1), "genero": "feminina" if m.group(1)[1] == "f" else "masculina",
                        "carater": "local", "idioma": "use --lang pt-br para pronúncia em português"})
        out = list({x["voice"]: x for x in out}.values())
    return out


def cmd_voices(args) -> int:
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    engines = parse_list(args.motores, ["edge", "gemini", "kokoro", "system"]) or ["edge", "gemini"]
    rows = []
    for eng in engines:
        vs = list_voices(eng, args.idioma)
        if args.so_nativas:
            vs = [v for v in vs if "multilíngue" not in v["idioma"] or eng == "gemini"]
        rows += vs[: args.limite] if args.limite else vs
    text = args.texto or "Olá! Esta é a minha voz para os seus tutoriais. Clique em Entrar no sistema e pronto."
    if args.amostras:
        samples = out_dir / "amostras"
        samples.mkdir(exist_ok=True)
        txt = samples / "_texto.txt"
        txt.write_text(text, encoding="utf-8")
        down: dict[str, str] = {}  # motor indisponível (sem chave/pacote): não tenta voz por voz
        for r in rows:
            if r["engine"] in down:
                r["amostra"], r["erro"] = None, down[r["engine"]]
                continue
            wav = samples / f"{r['engine']}-{kebab(r['voice'])}.wav"
            err, _ = TTS_ENGINES[r["engine"]](txt, wav, r["voice"], args.idioma.lower(), 1.0)
            if err and re.search(r"ausente|not installed|indisponível", err):
                down[r["engine"]] = err.strip()[:120]
            r["amostra"] = f"amostras/{wav.name}" if not err else None
            r["erro"] = (err or "").strip()[:120]
            if not err:  # mp3 leve para ouvir no celular
                mp3 = wav.with_suffix(".mp3")
                run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-b:a", "96k", str(mp3)])
                wav.unlink(missing_ok=True)
                r["amostra"] = f"amostras/{mp3.name}"
        txt.unlink(missing_ok=True)
    lines = [f"# Catálogo de vozes ({args.idioma})", "",
             f"Frase das amostras: “{text}”" if args.amostras else "", "",
             "| Motor | Voz | Gênero | Caráter | Idioma | Amostra | Flag |", "|---|---|---|---|---|---|---|"]
    for r in rows:
        amostra = f"[ouvir]({r['amostra']})" if r.get("amostra") else (f"falhou: {r['erro']}" if r.get("erro") else "—")
        lines.append(f"| {r['engine']} | {r['voice']} | {r['genero']} | {r['carater']} | {r['idioma']} | {amostra} | "
                     f"`--voz {r['engine']}:{r['voice']}` |")
    lines += ["", "Escolha uma voz e grave no projeto: `python tutorial.py config <projeto> --voz <motor>:<voz>`."
              " A escolha fica no tutorial.config.json e no Registro de decisões do ESTADO.md.", ""]
    (out_dir / "VOZES.md").write_text("\n".join(l for l in lines if l is not None), encoding="utf-8")
    ok = sum(1 for r in rows if r.get("amostra"))
    print(f"{out_dir / 'VOZES.md'}: {len(rows)} vozes" + (f", {ok} amostras geradas" if args.amostras else ""))
    return 0


def project_config(start: Path) -> dict:
    for d in (start, *start.parents):
        f = d / "tutorial.config.json"
        if f.exists():
            return load_json(f)
    return {}


def cmd_tts(args) -> int:
    script = Path(args.script)
    scenes = parse_script(script)
    cfg = project_config(script.parent).get("voice", {})
    engine = args.engine or cfg.get("engine", "auto")
    voice = args.voice or cfg.get("voice")
    speed = args.speed if args.speed is not None else float(cfg.get("speed", 1.0))
    lang = args.lang or cfg.get("lang", "pt-br")
    direction = cfg.get("direction") or next((l.split(":", 1)[1] for l in script.read_text(encoding="utf-8").splitlines()
                                              if l.lower().startswith("direção:")), "")
    if engine == "none":
        print("voz desativada (--voz nenhuma): durações virão do texto na tela")
        return 0
    order = TTS_FALLBACK if engine == "auto" else [engine]
    out_dir = Path(args.out) if args.out else script.parent / "audio"
    out_dir.mkdir(parents=True, exist_ok=True)
    durations, used = {}, None
    for s in scenes:
        if not s["narration"]:
            continue
        txt = out_dir / f"{s['id']}.txt"
        wav = out_dir / f"{s['id']}.wav"
        spoken, breaks = split_breaks(s["narration"])  # '|' só quebra a legenda; a voz não lê
        txt.write_text(spoken, encoding="utf-8")
        candidates = [used] if used else order
        words_out, err = None, "nenhum motor"
        for eng in candidates:
            v = voice if (engine != "auto" or eng == order[0]) else None
            err, words_out = TTS_ENGINES[eng](txt, wav, v, lang, speed, direction=direction, model=args.model)
            if not err:
                used = eng
                break
            print(f"aviso: motor '{eng}' indisponível: {err.strip()}", file=sys.stderr)
        if err:
            die(f"TTS falhou na cena {s['id']}: {err.strip()}")
        if used == "system":
            print("aviso: voz do sistema é robótica; use só como último recurso (veja --voz edge/gemini).", file=sys.stderr)
        if not words_out:
            words_out = align_words(wav, spoken, lang)
        if words_out:
            words_out = mark_breaks(words_out, breaks)
            (out_dir / f"{s['id']}.words.json").write_text(json.dumps(words_out, ensure_ascii=False, indent=1), encoding="utf-8")
        durations[s["id"]] = round(media_duration(wav), 3)
        print(f"{s['id']}: {durations[s['id']]:.2f} s  ({s['words']} palavras)  [{used}]"
              + ("" if words_out else "  (sem tempos por palavra)"))
    (out_dir / "durations.json").write_text(json.dumps(durations, indent=2), encoding="utf-8")
    (out_dir / "voice.json").write_text(json.dumps({"engine": used, "voice": voice, "speed": speed, "lang": lang},
                                                   indent=2), encoding="utf-8")
    print(f"total de fala: {sum(durations.values()):.1f} s → {out_dir / 'durations.json'}")
    return 0


def cmd_retime(args) -> int:
    proj = Path(args.project)
    sb_path = proj / "storyboard.json"
    sb = load_json(sb_path)
    durations = load_json(proj / "audio" / "durations.json")
    t = 0.0
    for sc in sb["scenes"]:
        old = sc["end"] - sc["start"]
        if sc["id"] in durations:
            length = max(MIN_SCENE, durations[sc["id"]] + args.gap + float(sc.get("extra", 0)))
        else:
            length = max(MIN_SCENE, old)
        sc["start"] = round(t, 3)
        t += length
        sc["end"] = round(t, 3)
    sb["meta"]["duration"] = round(t, 3)
    sb_path.write_text(json.dumps(sb, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"storyboard retemporizado: {len(sb['scenes'])} cenas, {t:.2f} s")
    return 0


def cmd_narration(args) -> int:
    """Monta audio/narration.wav posicionando o áudio de cada cena no seu início."""
    proj = Path(args.project)
    sb = load_json(proj / "storyboard.json")
    inputs, filters = [], []
    for sc in sb["scenes"]:
        a = sc.get("audio")
        if not a or not (proj / a).exists():
            continue
        idx = len(filters)  # índice da entrada no ffmpeg (cada uma ocupa "-i" + caminho)
        inputs += ["-i", str(proj / a)]
        delay = int(round(sc["start"] * 1000))
        filters.append(f"[{idx}:a]adelay={delay}|{delay}[a{idx}]")
    if not inputs:
        die("nenhum áudio de cena encontrado")
    n = len(filters)
    mix = "".join(f"[a{i}]" for i in range(n)) + f"amix=inputs={n}:normalize=0,apad=whole_dur={sb['meta']['duration']}[out]"
    out = proj / "audio" / "narration.wav"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(filters + [mix]),
           "-map", "[out]", "-t", str(sb["meta"]["duration"]), str(out)]
    r = run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        die(r.stderr.strip())
    print(f"{out} ({media_duration(out):.2f} s)")
    return 0


# ---------------------------------------------------------------- idiomas (mesma imagem, uma faixa de áudio e uma legenda por idioma)
#
# A imagem é renderizada uma vez (renders/<slug>.raw.mp4, sem legenda queimada). Para cada idioma:
#   idiomas/<lang>/traducao.json   narração traduzida por cena (o ÚNICO passo do agente; o resto é script)
#   idiomas/<lang>/audio/cNN.wav   voz da cena, acelerada só o necessário para caber no tempo da cena
#   idiomas/<lang>/faixa.m4a       narração + os mesmos efeitos da composição, no volume da faixa original
#   idiomas/<lang>/legenda.vtt     legenda com o tempo de cada palavra da voz
# O idioma de origem usa o áudio do próprio render e as palavras de audio/*.words.json.

IDIOMAS_PADRAO = ["pt-BR", "en-US", "es"]
IDIOMAS = {
    "pt-BR": {"nome": "Português", "voz": "pt-BR-FranciscaNeural"},
    "en-US": {"nome": "English", "voz": "en-US-AvaNeural"},
    "es": {"nome": "Español", "voz": "es-MX-DaliaNeural"},
}
IDIOMA_ALIAS = {"pt": "pt-BR", "pt-br": "pt-BR", "en": "en-US", "en-us": "en-US", "es": "es", "es-419": "es",
                "es-mx": "es", "es-es": "es"}
FIT_MARGEM = 0.25        # s de silêncio garantidos no fim de cada cena
FIT_MAX_VELOCIDADE = 1.25   # acima disso a fala soa apressada: a tradução da cena precisa ficar mais curta
TRADUCAO_REGRAS = ("Traduza só o campo 'texto' de cada cena, com o sentido e o tom do original, para quem vai seguir "
                   "a tela. Nomes de botões, menus e campos que aparecem na tela ficam em português, entre aspas, "
                   "como estão na interface. Mantenha o marcador '|' (quebra de legenda) em pontos equivalentes. "
                   "Frase do mesmo tamanho ou menor que a original: a fala precisa caber no tempo da cena.")


def norm_idioma(code: str) -> str:
    c = IDIOMA_ALIAS.get(code.strip().lower(), code.strip())
    if c not in IDIOMAS:
        die(f"idioma não suportado: {code} (use {', '.join(IDIOMAS)})")
    return c


def idiomas_do_projeto(proj: Path, pedido: str | None = None) -> tuple[str, list[str]]:
    cfg = project_config(proj)
    origem = norm_idioma(cfg.get("language") or "pt-BR")
    lista = [norm_idioma(x) for x in (pedido.split(",") if pedido else cfg.get("idiomas") or IDIOMAS_PADRAO)]
    lista = list(dict.fromkeys([origem] + lista)) if origem in lista else [origem] + list(dict.fromkeys(lista))
    return origem, lista


def short_hash(s: str) -> str:
    import hashlib
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:10]


def write_vtt(ws: list[dict], path: Path) -> int:
    def ts(t: float) -> str:
        return srt_time(t).replace(",", ".")
    lines = ["WEBVTT", ""]
    cues = group_cues(ws, 7, 3.4)
    for c in cues:
        lines += [f"{ts(c[0]['start'])} --> {ts(c[-1]['end'])}", " ".join(w["text"] for w in c), ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return len(cues)


def composition_effects(proj: Path) -> list[dict]:
    """Efeitos e trilha da composição (todo <audio> menos a narração 'vo'): arquivo, início e volume."""
    html = (proj / "composition" / "index.html").read_text(encoding="utf-8")
    out = []
    for tag in re.findall(r"<audio\b[^>]*>", html):
        attrs = dict(re.findall(r'([\w-]+)="([^"]*)"', tag))
        if attrs.get("id") == "vo" or not attrs.get("src"):
            continue
        src = proj / "composition" / attrs["src"]
        if src.exists():
            out.append({"src": src, "start": float(attrs.get("data-start", 0)),
                        "volume": float(attrs.get("data-volume", 1))})
    return out


def loudness(path: Path) -> float | None:
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "loudnorm=print_format=json", "-f", "null", "-"],
            capture_output=True, text=True)
    m = re.search(r'"input_i"\s*:\s*"(-?[\d.]+)"', r.stderr)
    return float(m.group(1)) if m else None


def idioma_voz(proj: Path, lang: str) -> str:
    return (project_config(proj).get("vozes_idioma") or {}).get(lang) or IDIOMAS[lang]["voz"]


def cmd_idiomas(args) -> int:
    proj = Path(args.project)
    sb = load_json(proj / "storyboard.json")
    slug = sb["meta"].get("slug") or proj.name
    raw = proj / "renders" / f"{slug}.raw.mp4"
    if not raw.exists():
        die(f"falta o render sem legenda {raw} (rode: tutorial.py render {proj})")
    origem, lista = idiomas_do_projeto(proj, args.idiomas)
    base = proj / "idiomas"
    dur_video = media_duration(raw)
    faltam: dict[str, list[str]] = {}

    # 1) traduções: cria/atualiza o esqueleto; texto vazio ou de narração antiga = pendente
    for lang in lista[1:]:
        f = base / lang / "traducao.json"
        old = {c["id"]: c for c in (load_json(f).get("cenas", []) if f.exists() else [])}
        cenas = []
        for sc in sb["scenes"]:
            if not sc.get("narration"):
                continue
            h = short_hash(sc["narration"])
            prev = old.get(sc["id"]) or {}
            texto = prev.get("texto", "") if prev.get("hash") == h else ""
            cenas.append({"id": sc["id"], "hash": h, "origem": sc["narration"], "segundos": round(sc["end"] - sc["start"], 2),
                          "texto": texto})
            if not texto.strip():
                faltam.setdefault(lang, []).append(sc["id"])
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps({"idioma": lang, "origem": origem, "regras": TRADUCAO_REGRAS, "cenas": cenas},
                                ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if faltam:
        for lang, ids in faltam.items():
            print(f"falta traduzir {lang}: {', '.join(ids)} → preencha 'texto' em {base / lang / 'traducao.json'}")
        return 3
    if args.preparar:
        print("traduções completas; rode sem --preparar para gerar voz, faixas e legendas")
        return 0

    # 2) idioma de origem: o áudio do render e as palavras da narração original
    src_dir = base / origem
    src_dir.mkdir(parents=True, exist_ok=True)
    faixa_src = src_dir / "faixa.m4a"
    if not faixa_src.exists() or faixa_src.stat().st_mtime < raw.stat().st_mtime:
        r = run(["ffmpeg", "-y", "-v", "error", "-i", str(raw), "-vn", "-c:a", "copy", str(faixa_src)], capture_output=True, text=True)
        if r.returncode:
            die(f"não consegui extrair o áudio de {raw}: {r.stderr[-300:]}")
    n = write_vtt(project_words(proj, sb), src_dir / "legenda.vtt")
    print(f"{origem}: faixa do render, legenda com {n} blocos")
    alvo_lufs = loudness(faixa_src)
    efeitos = composition_effects(proj)
    manifest = [{"idioma": origem, "nome": IDIOMAS[origem]["nome"], "faixa": f"{origem}/faixa.m4a",
                 "legenda": f"{origem}/legenda.vtt", "voz": "original"}]

    # 3) demais idiomas: voz por cena (cabendo no tempo), mixagem com os efeitos, legenda
    erros = []
    for lang in lista[1:]:
        erros_antes = len(erros)
        d = base / lang
        aud = d / "audio"
        aud.mkdir(parents=True, exist_ok=True)
        voz = idioma_voz(proj, lang)
        cache_f = aud / "vozes.json"
        cache = load_json(cache_f) if cache_f.exists() else {}
        tr = {c["id"]: c["texto"] for c in load_json(d / "traducao.json")["cenas"]}
        ws_all, entradas = [], []
        for sc in sb["scenes"]:
            if sc["id"] not in tr:
                continue
            spoken, breaks = split_breaks(tr[sc["id"]])
            cabe = sc["end"] - sc["start"] - FIT_MARGEM
            wav, words_f = aud / f"{sc['id']}.wav", aud / f"{sc['id']}.words.json"
            key = short_hash(f"{spoken}|{voz}|{cabe:.2f}")
            if cache.get(sc["id"], {}).get("key") != key or not wav.exists():
                txt = aud / f"{sc['id']}.txt"
                txt.write_text(spoken, encoding="utf-8")
                speed, ws = 1.0, None
                for _ in range(3):   # 1.0; depois a razão exata; depois um empurrão final
                    err, ws = tts_edge(txt, wav, voz, lang.lower(), speed)
                    if err:
                        die(f"voz {lang} falhou na cena {sc['id']}: {err}")
                    dur = media_duration(wav)
                    if dur <= cabe:
                        break
                    speed = round(max(speed + 0.03, speed * dur / cabe + 0.01), 3)
                    if speed > FIT_MAX_VELOCIDADE:
                        break
                if dur > cabe:
                    erros.append(f"{lang} {sc['id']}: a fala tem {dur:.1f} s e a cena {cabe:.1f} s mesmo a "
                                 f"{FIT_MAX_VELOCIDADE:.2f}× → encurte o 'texto' desta cena em {d / 'traducao.json'}")
                    continue
                words_f.write_text(json.dumps(mark_breaks(ws or [], breaks), ensure_ascii=False, indent=1), encoding="utf-8")
                cache[sc["id"]] = {"key": key, "dur": round(dur, 3), "velocidade": speed}
                print(f"  {lang} {sc['id']}: {dur:.2f} s / {cabe:.2f} s" + (f" (a {speed:.2f}×)" if speed > 1 else ""))
            entradas.append((wav, sc["start"]))
            for w in load_json(words_f):
                ws_all.append({"text": w["text"], "start": sc["start"] + w["start"], "end": sc["start"] + w["end"],
                               "scene": sc["id"], "brk": bool(w.get("brk"))})
        cache_f.write_text(json.dumps(cache, indent=1), encoding="utf-8")
        if len(erros) > erros_antes:
            continue
        # mixagem: mesma conta da composição (narração no início da cena + cada efeito no seu instante e volume)
        faixa = d / "faixa.m4a"
        mix_key = short_hash(json.dumps([[str(w), s, file_sig(w)] for w, s in entradas]
                                        + [[str(e["src"]), e["start"], e["volume"]] for e in efeitos]) + f"{dur_video:.3f}")
        if cache.get("_mix") != mix_key or not faixa.exists():
            inputs, chains = [], []
            for i, (w, s) in enumerate(entradas):
                ms = int(round(s * 1000))
                inputs += ["-i", str(w)]
                chains.append(f"[{i}:a]aresample=48000,adelay={ms}|{ms}[n{i}]")
            for j, e in enumerate(efeitos, len(entradas)):
                ms = int(round(e["start"] * 1000))
                inputs += ["-i", str(e["src"])]
                chains.append(f"[{j}:a]aresample=48000,volume={e['volume']},adelay={ms}|{ms}[n{j}]")
            k = len(chains)
            mix = "".join(f"[n{i}]" for i in range(k)) + f"amix=inputs={k}:normalize=0,apad=whole_dur={dur_video:.3f}[m]"
            tmp = d / "mix.wav"
            r = run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(chains + [mix]), "-map", "[m]",
                     "-ac", "2", "-t", f"{dur_video:.3f}", str(tmp)], capture_output=True, text=True)
            if r.returncode:
                die(f"mixagem {lang} falhou: {r.stderr[-400:]}")
            # mesmo volume percebido da faixa original (ninguém aumenta o som ao trocar de idioma)
            ganho = 0.0
            atual = loudness(tmp)
            if alvo_lufs is not None and atual is not None:
                ganho = round(alvo_lufs - atual, 2)
            r = run(["ffmpeg", "-y", "-v", "error", "-i", str(tmp), "-af", f"volume={ganho}dB,alimiter=limit=0.97",
                     "-c:a", "aac", "-b:a", "160k", "-ar", "48000", str(faixa)], capture_output=True, text=True)
            tmp.unlink(missing_ok=True)
            if r.returncode:
                die(f"codificação da faixa {lang} falhou: {r.stderr[-400:]}")
            cache["_mix"] = mix_key
            cache_f.write_text(json.dumps(cache, indent=1), encoding="utf-8")
        n = write_vtt(ws_all, d / "legenda.vtt")
        print(f"{lang}: faixa {media_duration(faixa):.2f} s (voz {voz}), legenda com {n} blocos")
        manifest.append({"idioma": lang, "nome": IDIOMAS[lang]["nome"], "faixa": f"{lang}/faixa.m4a",
                         "legenda": f"{lang}/legenda.vtt", "voz": voz})
    if erros:
        print("\n".join(erros))
        return 4
    (base / "idiomas.json").write_text(json.dumps({"origem": origem, "video": f"renders/{slug}.raw.mp4",
                                                   "idiomas": manifest}, ensure_ascii=False, indent=2) + "\n",
                                       encoding="utf-8")
    registrar(proj, f"idiomas: {', '.join(m['idioma'] for m in manifest)} (faixas e legendas em idiomas/)")
    print(f"{base / 'idiomas.json'}: {len(manifest)} idioma(s) sobre a mesma imagem")
    return 0


# ---------------------------------------------------------------- mídia

def cmd_frames(args) -> int:
    if not which("ffmpeg"):
        die("ffmpeg ausente")
    src = Path(args.video)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    # quadros para o agente olhar saem reduzidos (padrão 800 px): a imagem custa ~1/3 dos tokens e é relida a cada
    # turno seguinte; --largura 0 mantém o tamanho original (inspeção de legibilidade fina)
    sc = f",scale={args.largura}:-2" if args.largura else ""
    if args.at:
        for t in [float(x) for x in args.at.split(",")]:
            dst = out / f"at-{t:07.2f}s.png"
            run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(t), "-i", str(src), "-frames:v", "1", "-update", "1",
                 *(["-vf", sc[1:]] if sc else []), str(dst)])
    elif args.every:
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-vf", f"fps=1/{args.every}{sc}", str(out / "f%05d.png")])
    else:
        vf = f"select='gt(scene,{args.scene})',showinfo{sc}"
        r = run(["ffmpeg", "-y", "-i", str(src), "-vf", vf, "-vsync", "vfr", str(out / "scene%05d.png")],
                capture_output=True, text=True)
        times = re.findall(r"pts_time:([0-9.]+)", r.stderr)
        (out / "scene-times.json").write_text(json.dumps([float(t) for t in times]), encoding="utf-8")
        if len(times) < 3:
            # fades e zooms suaves não disparam o detector de corte: cai para intervalo fixo (~12 frames)
            step = max(1.0, round(media_duration(src) / 12, 1))
            print(f"detector de cena achou {len(times)} corte(s); usando 1 frame a cada {step} s")
            run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-vf", f"fps=1/{step}{sc}", str(out / "f%05d.png")])
    pngs = sorted(out.glob("*.png"))
    if args.sheet and pngs:
        contact_sheet(pngs, out / "contact-sheet.jpg")
    print(f"{len(pngs)} frames em {out}")
    return 0


def contact_sheet(pngs: list[Path], dst: Path, cols: int = 5, limit: int = 60) -> None:
    pngs = pngs[:limit]
    lst = dst.with_suffix(".txt")
    lst.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in pngs), encoding="utf-8")
    rows = max(1, (len(pngs) + cols - 1) // cols)
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
         "-vf", f"scale=384:-2,tile={cols}x{rows}", "-frames:v", "1", "-update", "1", str(dst)])
    lst.unlink(missing_ok=True)


def cmd_record(args) -> int:
    if not which("ffmpeg"):
        die("ffmpeg ausente")
    system = platform.system()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if system == "Windows":
        src = ["-f", "gdigrab", "-framerate", str(args.fps), "-i", f"title={args.window}" if args.window else "desktop"]
    elif system == "Darwin":
        src = ["-f", "avfoundation", "-framerate", str(args.fps), "-i", args.device or "1:none"]
    else:
        src = ["-f", "x11grab", "-framerate", str(args.fps), "-i", os.environ.get("DISPLAY", ":0.0")]
    cmd = ["ffmpeg", "-y", "-loglevel", "error", *src, "-t", str(args.seconds),
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", str(out)]
    print("gravando… (o usuário executa o fluxo agora)")
    r = run(cmd)
    return r.returncode


def cmd_reference(args) -> int:
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    src = args.source
    if re.match(r"https?://", src):
        if not which("yt-dlp"):
            die("yt-dlp ausente")
        base = ["yt-dlp", "--js-runtimes", "node"] if which("node") else ["yt-dlp"]
        run([*base, "--write-description", "-f", "bv*[height<=1080]+ba/b", "--merge-output-format", "mp4",
             "-o", str(out / "video.%(ext)s"), src])
        video = next(iter(sorted(out.glob("video.*"))), None)
        if not video:
            die("download falhou")
    else:
        video = Path(src)
        if not video.exists():
            die(f"arquivo não encontrado: {video}")
    audio = out / "audio.wav"
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", str(audio)])
    transcribe(audio, out / "transcript.json", out / "transcript.srt", args.lang, args.model)
    frames_args = argparse.Namespace(video=str(video), out=str(out / "frames"), at=None,
                                     every=args.every, scene=args.scene, sheet=True, largura=800)
    cmd_frames(frames_args)
    print(f"referência pronta em {out}")
    return 0


# ---------------------------------------------------------------- transcrição e legendas

def transcribe(media: Path, json_out: Path, srt_out: Path | None, lang: str | None, model: str) -> list[dict]:
    try:
        from faster_whisper import WhisperModel
    except Exception:
        WhisperModel = None
    segments: list[dict] = []
    if WhisperModel is not None:
        m = WhisperModel(model, device="cpu", compute_type="int8")
        segs, _info = m.transcribe(str(media), language=lang, vad_filter=True, word_timestamps=True)
        for s in segs:
            segments.append({
                "start": round(s.start, 3), "end": round(s.end, 3), "text": s.text.strip(),
                "words": [{"text": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)}
                          for w in (s.words or [])],
            })
    elif which("npx"):
        tmp = json_out.with_suffix(".hf.json")
        hf_model = "small.en" if (lang or "en").startswith("en") else "large-v3"
        r = run(["npx", "--yes", "hyperframes", "transcribe", str(media), "--json", "-m", hf_model]
                + (["-l", lang] if lang else []), capture_output=True, text=True)
        if r.returncode != 0:
            die(f"transcrição falhou: {r.stderr[-400:]}")
        tmp.write_text(r.stdout, encoding="utf-8")
        segments = transcript_segments(json.loads(r.stdout))
    else:
        die("nem faster-whisper nem npx disponíveis para transcrever")
    json_out.write_text(json.dumps({"segments": segments}, ensure_ascii=False, indent=2), encoding="utf-8")
    if srt_out:
        write_srt(segments, srt_out)
    return segments


def transcript_segments(data) -> list[dict]:
    """Aceita {segments:[...]}, lista de segmentos ou {words:[...]} e devolve segmentos."""
    if isinstance(data, dict) and "segments" in data:
        return data["segments"]
    if isinstance(data, list) and data and "start" in data[0]:
        return data
    if isinstance(data, dict) and "words" in data:
        ws = [{"text": w.get("text") or w.get("word", ""), "start": w["start"], "end": w["end"]} for w in data["words"]]
        return [{"start": ws[0]["start"], "end": ws[-1]["end"], "text": " ".join(w["text"] for w in ws), "words": ws}] if ws else []
    die("formato de transcrição não reconhecido")
    return []


def srt_time(t: float) -> str:
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_srt(segments: list[dict], path: Path, max_words: int = 7, max_dur: float = 3.5) -> None:
    cues = []
    for seg in segments:
        ws = seg.get("words") or [{"text": seg["text"], "start": seg["start"], "end": seg["end"]}]
        cur = []
        for w in ws:
            cur.append(w)
            punct = w["text"].rstrip().endswith((".", "!", "?", ",", ";", ":"))
            if len(cur) >= max_words or (cur[-1]["end"] - cur[0]["start"]) >= max_dur or punct:
                cues.append(cur)
                cur = []
        if cur:
            cues.append(cur)
    lines = []
    for i, c in enumerate(cues, 1):
        text = " ".join(w["text"].strip() for w in c).strip()
        lines += [str(i), f"{srt_time(c[0]['start'])} --> {srt_time(c[-1]['end'])}", text, ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_srt(path: Path) -> list[tuple[float, float, str]]:
    def secs(s):
        h, m, rest = s.split(":")
        sec, ms = rest.split(",")
        return int(h) * 3600 + int(m) * 60 + int(sec) + int(ms) / 1000
    cues = []
    for block in re.split(r"\n\s*\n", path.read_text(encoding="utf-8").strip()):
        m = re.search(r"(\d+:\d+:\d+,\d+)\s*-->\s*(\d+:\d+:\d+,\d+)", block)
        if m:
            text = block.split(m.group(0), 1)[1].strip()
            cues.append((secs(m.group(1)), secs(m.group(2)), text))
    return cues


def cmd_captions(args) -> int:
    media = Path(args.media)
    srt = Path(args.out) if args.out else media.with_suffix(".srt")
    transcribe(media, srt.with_suffix(".transcript.json"), srt, args.lang, args.model)
    print(f"legendas: {srt}")
    return 0


# ---------------------------------------------------------------- legendas queimadas

CAPTION_STYLES = ("bold-pop", "highlight", "word-by-word", "clean", "boxed")


def ass_color(hex_color: str, alpha: int = 0) -> str:
    h = hex_color.lstrip("#")
    r, g, b = h[0:2], h[2:4], h[4:6]
    return f"&H{alpha:02X}{b}{g}{r}".upper()


def ass_time(t: float) -> str:
    cs = int(round(max(t, 0) * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def project_words(proj: Path, sb: dict) -> list[dict]:
    """Palavras com tempo absoluto no vídeo, a partir de audio/<cena>.words.json + início da cena."""
    out = []
    for sc in sb["scenes"]:
        f = proj / "audio" / f"{sc['id']}.words.json"
        if not f.exists():
            continue
        for w in load_json(f):
            out.append({"text": w["text"], "start": sc["start"] + w["start"], "end": sc["start"] + w["end"],
                        "scene": sc["id"], "brk": bool(w.get("brk"))})
    return out


def group_cues(ws: list[dict], max_words: int, max_dur: float) -> list[list[dict]]:
    """Blocos de legenda: quebram no marcador '|' do roteiro, em pontuação, pausa > 0,6 s,
    limite de palavras/duração e mudança de cena."""
    cues, cur = [], []
    for w in ws:
        if cur and (w["start"] - cur[-1]["end"] > 0.6 or w.get("scene") != cur[-1].get("scene")):
            cues.append(cur)
            cur = []
        cur.append(w)
        # nome de botão entre aspas ("Enviar link de recuperação") não se parte em dois blocos
        aspas = sum(x["text"].count('"') + x["text"].count("“") + x["text"].count("”") for x in cur) % 2 == 1
        limite = not aspas and (len(cur) >= max_words or cur[-1]["end"] - cur[0]["start"] >= max_dur)
        if (w.get("brk") or limite
                or (not aspas and w["text"].rstrip().endswith((".", "!", "?", ",", ";", ":")))):
            cues.append(cur)
            cur = []
    if cur:
        cues.append(cur)
    return cues


CAPTION_POSITIONS = {"bottom": 2, "middle": 5, "top": 8}   # alinhamento ASS (numpad)
CAPTION_SIZES = {"p": 0.82, "m": 1.0, "g": 1.22}
# ordem de tentativa do modo auto: base é o lugar esperado; topo é a fuga; meio só se as duas cobrirem o foco
AUTO_ORDER = ("bottom", "top", "middle")
FOCUS_PAD = 0.02          # folga em volta do foco, fração da altura do quadro
ZOOM_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*[×x]")


def caption_metrics(style: str, w: int, h: int, position: str, size_key: str = "m",
                    margin_px: int | None = None, top_px: int | None = None) -> dict:
    """Geometria da legenda no quadro (a mesma que vai para o .ass): corpo, margem vertical e lateral."""
    k = min(w, h) / 1080
    vertical = h > w
    base = {
        "clean": dict(size=52, bold=0, outline=3, shadow=1, border=1, back="&H80000000", margin=70),
        "boxed": dict(size=50, bold=1, outline=16, shadow=0, border=3, back="&H50101010", margin=70),
        "bold-pop": dict(size=84, bold=1, outline=7, shadow=2, border=1, back="&H80000000", margin=230 if vertical else 150),
        "highlight": dict(size=60, bold=1, outline=2, shadow=3, border=1, back="&HA0000000", margin=90),
        "word-by-word": dict(size=64, bold=1, outline=3, shadow=3, border=1, back="&HA0000000", margin=110),
    }[style]
    size = round(base["size"] * k * (1.25 if vertical else 1) * CAPTION_SIZES[size_key])
    margin = round((base["margin"] if position == "bottom" else 90) * k)
    # zonas seguras do canal (ex.: interface do Reels cobre a base e o topo)
    if position == "bottom" and margin_px is not None:
        margin = max(margin, margin_px)
    if position == "top" and top_px is not None:
        margin = max(margin, top_px)
    return {"k": k, "base": base, "size": size, "margin": margin, "side": round(120 * k),
            "outline": round(base["outline"] * k)}


def caption_rect(text: str, style: str, w: int, h: int, position: str, size_key: str = "m", case: str = "normal",
                 margin_px: int | None = None, top_px: int | None = None) -> list[float]:
    """Retângulo [x, y, w, h] que o bloco ocupa no quadro. Estimativa conservadora da largura do texto
    (sem medir a fonte): 0,56 do corpo por caractere (0,66 em CAIXA ALTA), +12 % no bold-pop pela palavra ampliada."""
    m = caption_metrics(style, w, h, position, size_key, margin_px, top_px)
    size = m["size"]
    char_w = size * (0.66 if case == "upper" else 0.56) * (1.12 if style == "bold-pop" else 1)
    usable = w - 2 * m["side"]
    text_w = len(text) * char_w
    lines = max(1, -(-text_w // usable))
    pad = m["outline"] + round(8 * m["k"])
    rw, rh = min(text_w, usable) + 2 * pad, lines * size * 1.25 + 2 * pad
    y = h - m["margin"] - rh if position == "bottom" else m["margin"] if position == "top" else (h - rh) / 2
    return [round((w - rw) / 2, 1), round(y, 1), round(rw, 1), round(rh, 1)]


def overlap_area(a: list[float], b: list[float], pad: float = 0.0) -> float:
    dx = min(a[0] + a[2], b[0] + b[2] + pad) - max(a[0], b[0] - pad)
    dy = min(a[1] + a[3], b[1] + b[3] + pad) - max(a[1], b[1] - pad)
    return dx * dy if dx > 0 and dy > 0 else 0.0


def scene_zoom(sc: dict) -> float:
    if sc.get("zoom"):
        return float(sc["zoom"])
    m = ZOOM_RE.search(sc.get("camera", "") or "")
    return float(m.group(1).replace(",", ".")) if m and "zoom" in sc.get("camera", "").lower() else 1.0


def scene_focus_boxes(sb: dict, step_map: dict | None) -> dict[str, list[dict]]:
    """Áreas que a legenda não pode cobrir, por cena, em pixels do quadro-mestre.

    Fontes, nesta ordem: `focus_boxes` da cena (já em pixels do quadro: callouts, chips, o que o agente
    desenhar por cima); o `target_box` de cada passo da cena, levado da captura para o quadro pelo
    `screen_box` (cena ou meta: onde o screenshot aparece no vídeo; padrão: encaixado no quadro inteiro)
    e ampliado pelo zoom da cena em torno do próprio centro (punch-in com transform-origin no alvo)."""
    W, H = int(sb["meta"]["width"]), int(sb["meta"]["height"])
    steps = {s["id"]: s for s in (step_map or {}).get("steps", [])}
    cap_res = (step_map or {}).get("target", {}).get("capture_resolution") or [W, H]
    out: dict[str, list[dict]] = {}
    for sc in sb.get("scenes", []):
        boxes = [{"box": [float(v) for v in b], "src": "focus_boxes"} for b in sc.get("focus_boxes", [])]
        zoom = scene_zoom(sc)
        for st in sc.get("steps", []):
            tb = steps.get(st, {}).get("target_box")
            if not tb:
                continue
            cw, ch = steps[st].get("capture_resolution") or cap_res
            screen = sc.get("screen_box") or sb["meta"].get("screen_box")
            if not screen:
                s = min(W / cw, H / ch)
                screen = [(W - cw * s) / 2, (H - ch * s) / 2, cw * s, ch * s]
            sx, sy = screen[2] / cw, screen[3] / ch
            fw, fh = tb[2] * sx * zoom, tb[3] * sy * zoom
            cx, cy = screen[0] + (tb[0] + tb[2] / 2) * sx, screen[1] + (tb[1] + tb[3] / 2) * sy
            x0, y0 = max(0.0, cx - fw / 2), max(0.0, cy - fh / 2)
            x1, y1 = min(float(W), cx + fw / 2), min(float(H), cy + fh / 2)
            if x1 > x0 and y1 > y0:
                boxes.append({"box": [round(x0, 1), round(y0, 1), round(x1 - x0, 1), round(y1 - y0, 1)],
                              "src": f"target_box {st}"})
        out[sc["id"]] = boxes
    return out


def map_focus_boxes(boxes: dict[str, list[dict]], fn) -> dict[str, list[dict]]:
    """Leva as áreas de foco do quadro-mestre para o quadro de uma saída (fn: box → box ou None)."""
    out = {}
    for sid, bs in boxes.items():
        out[sid] = [{**b, "box": nb} for b in bs if (nb := fn(b["box"])) is not None]
    return out


def place_captions(cues: list[list[dict]], style: str, w: int, h: int, position: str, size_key: str, case: str,
                   focus: dict[str, list[dict]], scene_pos: dict[str, str] | None = None,
                   margin_px: int | None = None, top_px: int | None = None) -> list[dict]:
    """Decide a posição de cada bloco. `auto`: a legenda não pula dentro de uma cena; vale a primeira de
    base → topo → meio que não cobre nenhum foco em nenhum bloco da cena. Se nenhuma serve para a cena
    inteira, cada bloco pega a primeira livre para ele ou, sem saída, a de menor área coberta (a colisão
    fica registrada). Posição fixa (flag ou `caption_position` da cena) é respeitada; só registra colisões."""
    pad = FOCUS_PAD * h

    def try_pos(cue: list[dict], pos: str) -> dict:
        text = " ".join(x["text"] for x in cue)
        r = caption_rect(text, style, w, h, pos, size_key, case, margin_px, top_px)
        hits = [b for b in focus.get(cue[0].get("scene"), []) if overlap_area(r, b["box"], pad) > 0]
        return {"position": pos, "rect": r, "hits": hits, "area": sum(overlap_area(r, b["box"], pad) for b in hits)}

    def best_for(cue: list[dict], order) -> dict:
        best = None
        for pos in order:
            t = try_pos(cue, pos)
            if best is None or t["area"] < best["area"]:
                best = t
            if not t["hits"]:
                break
        return best

    by_scene: dict[str, list[int]] = {}
    for i, cue in enumerate(cues):
        by_scene.setdefault(cue[0].get("scene"), []).append(i)
    chosen: dict[int, dict] = {}
    fixed_of = {}
    for sid, idx in by_scene.items():
        fixed = (scene_pos or {}).get(sid) or (position if position != "auto" else None)
        fixed_of[sid] = fixed
        if fixed:
            chosen.update({i: try_pos(cues[i], fixed) for i in idx})
            continue
        for pos in AUTO_ORDER:
            trial = {i: try_pos(cues[i], pos) for i in idx}
            if not any(t["hits"] for t in trial.values()):
                chosen.update(trial)
                break
        else:
            chosen.update({i: best_for(cues[i], AUTO_ORDER) for i in idx})
    out = []
    for i, cue in enumerate(cues):
        c, sid = chosen[i], cue[0].get("scene")
        out.append({"scene": sid, "start": round(cue[0]["start"], 3), "end": round(cue[-1]["end"], 3),
                    "text": " ".join(x["text"] for x in cue), "position": c["position"], "rect": c["rect"],
                    "auto": not fixed_of[sid], "collisions": [{"src": b["src"], "box": b["box"]} for b in c["hits"]]})
    return out


def project_focus_boxes(proj: Path, sb: dict) -> dict[str, list[dict]]:
    sm = proj / "step-map.json"
    return scene_focus_boxes(sb, load_json(sm) if sm.exists() else None)


def scene_caption_positions(sb: dict) -> dict[str, str]:
    """`caption_position` por cena no storyboard (base/topo/meio ou bottom/top/middle) fixa a posição dela."""
    alias = {"base": "bottom", "topo": "top", "meio": "middle"}
    out = {}
    for sc in sb.get("scenes", []):
        p = alias.get(sc.get("caption_position", ""), sc.get("caption_position"))
        if p in CAPTION_POSITIONS:
            out[sc["id"]] = p
    return out


def write_placements(path: Path, placements: list[dict], w: int, h: int, position: str) -> None:
    """Registro de onde cada bloco foi parar e por quê: evidência para o audit e para o veredito."""
    path.write_text(json.dumps({"frame": [w, h], "position": position, "cues": placements}, ensure_ascii=False,
                               indent=1), encoding="utf-8")
    count = {p: sum(1 for c in placements if c["position"] == p) for p in CAPTION_POSITIONS}
    hit = [c for c in placements if c["collisions"]]
    print(f"legenda: {count['bottom']} bloco(s) na base, {count['top']} no topo, {count['middle']} no meio"
          + (f" · [AVISO] {len(hit)} bloco(s) cobrindo o foco (rode: tutorial.py audit captions)" if hit else ""))


def build_ass(cues: list[list[dict]], style: str, w: int, h: int, font: str, accent: str, case: str,
              position: str = "bottom", size_key: str = "m", margin_px: int | None = None,
              placements: list[dict] | None = None, top_px: int | None = None) -> str:
    """`placements` (de place_captions) põe cada bloco na sua posição com override \\an + MarginV por linha."""
    style_pos = "bottom" if position == "auto" else position
    m = caption_metrics(style, w, h, style_pos, size_key, margin_px, top_px)
    k, base, size, margin = m["k"], m["base"], m["size"], m["margin"]
    align = CAPTION_POSITIONS[style_pos]
    ph = h
    outline_col = "&H00101010" if style != "boxed" else "&H50101010"
    head = (
        "[Script Info]\nScriptType: v4.00+\nWrapStyle: 0\nScaledBorderAndShadow: yes\n"
        f"PlayResX: {w}\nPlayResY: {h}\n\n[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
        "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, "
        "MarginV, Encoding\n"
        f"Style: Cap,{font},{size},&H00FFFFFF,&H00FFFFFF,{outline_col},{base['back']},{-1 if base['bold'] else 0},0,0,0,"
        f"100,100,0,0,{base['border']},{round(base['outline'] * k)},{round(base['shadow'] * k)},{align},{round(120 * k)},"
        f"{round(120 * k)},{margin},1\n\n[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )

    def fmt(t: str) -> str:
        t = t.replace("{", "(").replace("}", ")")
        return t.upper() if case == "upper" else t.lower() if case == "lower" else t

    acc = ass_color(accent)
    # acento escuro (ex.: azul-marinho da marca) some sobre o contorno escuro: a palavra ativa fica branca
    # com contorno grosso na cor da marca, mantendo contraste e identidade
    h = accent.lstrip("#")
    lum = sum(c * int(h[i:i + 2], 16) / 255 for c, i in ((0.2126, 0), (0.7152, 2), (0.0722, 4)))
    dark_accent = lum < 0.35
    lines = []
    for ci, cue in enumerate(cues):
        nxt = cues[ci + 1][0]["start"] if ci + 1 < len(cues) else cue[-1]["end"] + 0.6
        cue_end = min(cue[-1]["end"] + 0.25, nxt)
        tag, mv = "", 0
        if placements:  # posição do bloco: n na linha + MarginV da posição (0 = a do estilo)
            pos = placements[ci]["position"]
            tag = f"{{\\an{CAPTION_POSITIONS[pos]}}}"
            mv = caption_metrics(style, w, ph, pos, size_key, margin_px, top_px)["margin"]
        if style in ("clean", "boxed"):
            text = " ".join(fmt(x["text"]) for x in cue)
            lines.append(f"Dialogue: 0,{ass_time(cue[0]['start'])},{ass_time(cue_end)},Cap,,0,0,{mv},,{tag}{text}")
            continue
        for i, cw in enumerate(cue):
            t0 = cue[0]["start"] if i == 0 else cw["start"]
            t1 = cue[i + 1]["start"] if i + 1 < len(cue) else cue_end
            parts = []
            for j, x in enumerate(cue):
                word = fmt(x["text"])
                if style == "word-by-word" and j > i:
                    break
                if j == i and style == "bold-pop" and dark_accent:
                    parts.append(f"{{\\3c{acc}\\bord{round(14 * k)}\\fscx112\\fscy112}}{word}{{\\r}}")
                elif j == i and style == "bold-pop":
                    parts.append(f"{{\\c{acc}\\fscx112\\fscy112}}{word}{{\\r}}")
                elif j == i and style == "word-by-word" and dark_accent:
                    parts.append(f"{{\\3c{acc}\\bord{round(10 * k)}}}{word}{{\\r}}")
                elif j == i and style == "highlight":
                    parts.append(f"{{\\3c{acc}\\bord{round(12 * k)}}}{word}{{\\r}}")
                elif j == i and style == "word-by-word":
                    parts.append(f"{{\\c{acc}}}{word}{{\\r}}")
                else:
                    parts.append(word)
            lines.append(f"Dialogue: 0,{ass_time(t0)},{ass_time(t1)},Cap,,0,0,{mv},,{tag}{' '.join(parts)}")
    return head + "\n".join(lines) + "\n"


def cmd_burn(args) -> int:
    proj = Path(args.project)
    sb = load_json(proj / "storyboard.json")
    cfg = project_config(proj).get("captions", {})
    style = args.style or cfg.get("style") or ("bold-pop" if sb["meta"]["height"] > sb["meta"]["width"] else "highlight")
    if style == "none":
        print("legendas queimadas desativadas (--legenda nenhuma); só o .srt será gerado")
    slug = sb["meta"].get("slug") or proj.name
    raw = Path(args.input) if args.input else proj / "renders" / f"{slug}.raw.mp4"
    out = Path(args.out) if args.out else proj / "renders" / f"{slug}.mp4"
    if not raw.exists():
        die(f"render de entrada não encontrado: {raw} (rode: tutorial.py render {proj})")
    out.parent.mkdir(parents=True, exist_ok=True)
    ws = project_words(proj, sb)
    if not ws:
        print("sem audio/*.words.json: transcrevendo o render com Whisper")
        segs = transcribe(raw, proj / "renders" / f"{slug}.transcript.json", None, (args.lang or "pt")[:2], "small")
        ws = [w for s in segs for w in s.get("words", [])]
    if not ws:
        die("nenhuma palavra para legendar")
    srt_lines = []
    for i, c in enumerate(group_cues(ws, 7, 3.4), 1):
        srt_lines += [str(i), f"{srt_time(c[0]['start'])} --> {srt_time(c[-1]['end'])}",
                      " ".join(w["text"] for w in c), ""]
    out.with_suffix(".srt").write_text("\n".join(srt_lines), encoding="utf-8")
    if style == "none":
        shutil.copyfile(raw, out)
        print(f"{out} (sem legenda queimada) + {out.with_suffix('.srt').name}")
        return 0
    max_words = {"bold-pop": 3, "highlight": 5, "word-by-word": 6}.get(style, 7)
    cues = group_cues(ws, max_words, 2.6 if style == "bold-pop" else 3.4)
    position = args.position or cfg.get("position", "auto")
    size_key = args.size or cfg.get("size", "m")
    case = args.case or cfg.get("case", "normal")
    W, H = int(sb["meta"]["width"]), int(sb["meta"]["height"])
    placements = place_captions(cues, style, W, H, position, size_key, case, project_focus_boxes(proj, sb),
                                scene_caption_positions(sb))
    ass = build_ass(cues, style, W, H, args.font or cfg.get("font", "Segoe UI"),
                    args.accent or cfg.get("accent", "#FFD43B"), case, position, size_key, placements=placements)
    ass_path = out.with_suffix(".ass")
    ass_path.write_text(ass, encoding="utf-8")
    write_placements(out.with_suffix(".captions.json"), placements, W, H, position)
    # subtitles= com caminho relativo e cwd na pasta evita o escape de "C:\" no filtro do ffmpeg
    r = subprocess.run([which("ffmpeg") or "ffmpeg", "-y", "-loglevel", "error", "-i", str(raw.resolve()),
                        "-vf", f"subtitles={ass_path.name}", "-c:v", "libx264", "-crf", "16", "-preset", "medium",
                        "-pix_fmt", "yuv420p", "-c:a", "copy", str(out.resolve())],
                       cwd=str(ass_path.parent), capture_output=True, text=True)
    if r.returncode != 0:
        die(f"ffmpeg falhou ao queimar a legenda: {r.stderr[-500:]}")
    print(f"{out} (legenda '{style}', {len(cues)} blocos) + {out.with_suffix('.srt').name}")
    return 0


# ---------------------------------------------------------------- saídas: formatos, resoluções, canais

CRF = {"1080p": 18, "720p": 19, "480p": 20}
LEVEL = {"1080p": "4.1", "720p": "4.0", "480p": "3.1"}
# menor texto de leitura da interface na saída; calibrado olhando frames reais: ≥14 legível, 10–14 no limite, <10 ilegível
LEGIBLE_PX, LIMIT_PX = 14, 10


def fmt_key(fmt: str) -> str:
    return fmt.replace(":", "x")


def legibility(px: float) -> str:
    return "legível" if px >= LEGIBLE_PX else "no limite" if px >= LIMIT_PX else "ilegível"


def output_geometry(mw: int, mh: int, W: int, H: int, mode: str, top_f: float = 0.0, base_f: float = 0.0,
                    recorte: float | None = None) -> dict:
    """Como o quadro-mestre (mw×mh) vira o quadro da saída (W×H). `reenquadrar` recorta a zona central de
    conteúdo do mestre (por padrão 2/3 da largura em 16:9) e encaixa no novo quadro, sobre o próprio vídeo
    desfocado; a faixa útil respeita as zonas seguras do canal."""
    if mode in ("escalar", "nativo"):
        return {"mode": mode, "scale": W / mw, "x0": 0, "cw": mw, "ch": mh, "fw": W, "fh": H, "ox": 0, "y": 0}
    ratio = recorte or (1280 / 1080 if mw > mh else mw / mh)
    cw = min(mw, int(round(mh * ratio / 2) * 2))
    ch = mh
    band_top, band_h = int(top_f * H), int(H * (1 - top_f - base_f))
    scale = min(W / cw, band_h / ch)
    fw, fh = int(cw * scale / 2) * 2, int(ch * scale / 2) * 2
    return {"mode": mode, "scale": scale, "x0": (mw - cw) // 2, "cw": cw, "ch": ch, "fw": fw, "fh": fh,
            "ox": (W - fw) // 2, "y": band_top + max(0, (band_h - fh) // 2)}


def safe_margins(H: int, top_f: float, base_f: float) -> tuple[int | None, int | None]:
    """Margens mínimas da legenda (base, topo) para fugir da interface do canal."""
    return (int(base_f * H + 0.03 * H) if base_f else None, int(top_f * H + 0.03 * H) if top_f else None)


def output_focus_boxes(proj: Path, sb: dict, mode: str, g: dict, fmt: str) -> dict[str, list[dict]]:
    """Áreas de foco no quadro de uma saída. No modo `nativo` a composição é outra: valem só as
    `focus_boxes_<formato>` da cena (ex.: `focus_boxes_9x16`), em pixels do quadro dessa saída."""
    if mode == "nativo":
        key = f"focus_boxes_{fmt_key(fmt)}"
        return {sc["id"]: [{"box": [float(v) for v in b], "src": key} for b in sc.get(key, [])]
                for sc in sb.get("scenes", [])}
    s, x0, ox, y = g["scale"], g["x0"], g["ox"], g["y"]

    def fn(b):
        x_a, x_b = max(b[0], x0), min(b[0] + b[2], x0 + g["cw"])
        if x_b <= x_a:
            return None  # o foco ficou fora do recorte
        return [round((x_a - x0) * s + ox, 1), round(b[1] * s + y, 1), round((x_b - x_a) * s, 1), round(b[3] * s, 1)]
    return map_focus_boxes(project_focus_boxes(proj, sb), fn)


def export_one(proj: Path, sb: dict, cfg: dict, saida: dict, args) -> dict:
    slug = sb["meta"].get("slug") or proj.name
    fmt, res = saida["formato"], saida["resolucao"]
    W, H = output_dims(fmt, res)
    native = proj / "renders" / f"{slug}-{fmt_key(fmt)}.raw.mp4"
    master_fmt = cfg.get("format", "16:9")
    src = native if native.exists() else proj / "renders" / f"{slug}.raw.mp4"
    if not src.exists():
        die(f"render-mestre não encontrado: {src} (rode: tutorial.py render {proj})")
    info = ffprobe(src)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    mw, mh = int(v["width"]), int(v["height"])
    mode = args.modo if args.modo != "auto" else ("nativo" if native.exists() else
                                                  "escalar" if abs(mw / mh - W / H) < 0.01 else "reenquadrar")
    top_f, base_f = saida.get("seguro_topo", 0.0), saida.get("seguro_base", 0.0)
    g = output_geometry(mw, mh, W, H, mode, top_f, base_f, args.recorte)
    scale = g["scale"]
    if mode in ("escalar", "nativo"):
        vf = f"[0:v]scale={W}:{H}:flags=lanczos" + (",unsharp=3:3:0.35" if scale < 0.95 else "") + "[v]"
    else:
        cw, ch, fw, fh, y = g["cw"], g["ch"], g["fw"], g["fh"], g["y"]
        vf = (f"[0:v]split[a][b];"
              f"[a]scale={W}:{H}:force_original_aspect_ratio=increase:flags=bilinear,crop={W}:{H},gblur=sigma=38,"
              f"eq=brightness=-0.04:saturation=0.85[bg];"
              f"[b]crop={cw}:{ch}:{(mw - cw) // 2}:0,scale={fw}:{fh}:flags=lanczos"
              + (",unsharp=3:3:0.35" if scale < 0.95 else "") + f"[fg];"
              f"[bg][fg]overlay=x=({W}-w)/2:y={y}[v]")
    cap = cfg.get("captions", {})
    style = args.legenda or saida.get("legenda") or cap.get("style") or ("bold-pop" if H > W else "highlight")
    style = "none" if style == "nenhuma" else style
    out = proj / "renders" / f"{slug}-{fmt_key(fmt)}-{res}.mp4"
    filters = vf
    ws = project_words(proj, sb)
    if style != "none" and ws:
        max_words = {"bold-pop": 3, "highlight": 5, "word-by-word": 6}.get(style, 7)
        cues = group_cues(ws, max_words, 2.6 if style == "bold-pop" else 3.4)
        position, size_key, case = cap.get("position", "auto"), saida.get("tamanho") or cap.get("size", "m"), cap.get("case", "normal")
        margin_px, top_px = safe_margins(H, top_f, base_f)
        focus = output_focus_boxes(proj, sb, mode, g, fmt)
        placements = place_captions(cues, style, W, H, position, size_key, case, focus, scene_caption_positions(sb),
                                    margin_px, top_px)
        ass = build_ass(cues, style, W, H, cap.get("font", "Segoe UI"), cap.get("accent", "#FFD43B"), case, position,
                        size_key, margin_px, placements=placements, top_px=top_px)
        ass_path = out.with_suffix(".ass")
        ass_path.write_text(ass, encoding="utf-8")
        write_placements(out.with_suffix(".captions.json"), placements, W, H, position)
        filters = vf.replace("[v]", "[vs]") + f";[vs]subtitles={ass_path.name}[v]"
    lufs = saida.get("lufs", -14)
    enc = ["-c:v", "libx264", "-preset", "slow", "-crf", str(CRF[res]), "-profile:v", "high", "-level", LEVEL[res],
           "-pix_fmt", "yuv420p", "-r", str(sb["meta"]["fps"]), "-movflags", "+faststart",
           "-c:a", "aac", "-b:a", "128k" if res == "480p" else "160k", "-ar", "48000"]
    if saida.get("maxrate"):
        enc += ["-maxrate", saida["maxrate"], "-bufsize", str(int(saida["maxrate"].rstrip("M")) * 2) + "M"]
    r = subprocess.run([which("ffmpeg") or "ffmpeg", "-y", "-loglevel", "error", "-i", str(src.resolve()),
                        "-filter_complex", filters, "-map", "[v]", "-map", "0:a?",
                        "-af", f"loudnorm=I={lufs}:TP=-1.5:LRA=11", *enc, str(out.resolve())],
                       cwd=str(out.parent), capture_output=True, text=True)
    if r.returncode != 0:
        die(f"ffmpeg falhou em {out.name}: {r.stderr[-600:]}")
    srt = proj / "renders" / f"{slug}.srt"
    if srt.exists():
        shutil.copyfile(srt, out.with_suffix(".srt"))
    if mode == "nativo" and fmt in CAPTURE_VIEWPORTS:
        # mestre nativo: o menor texto da tela capturada (≈10 px CSS em mobile) × escala da captura até o quadro
        ui_px = float(cfg.get("texto_minimo_css_px", 10)) * (mw / CAPTURE_VIEWPORTS[fmt]["width"]) * scale
    else:
        ui_px = float(cfg.get("texto_minimo_px", 24)) * scale
    dur = float(ffprobe(out)["format"]["duration"])
    warn = ""
    if saida.get("max_s") and dur > saida["max_s"]:
        warn = f"duração {dur:.0f} s acima do limite de {saida['max_s']} s do canal"
    return {"arquivo": out.name, "formato": fmt, "resolucao": res, "dims": f"{W}x{H}", "modo": mode,
            "legenda": style, "canal": saida.get("canal"), "mb": round(out.stat().st_size / 1e6, 1),
            "texto_ui_px": round(ui_px, 1), "legibilidade": legibility(ui_px), "aviso": warn}


def cmd_export(args) -> int:
    proj = Path(args.project)
    sb = load_json(proj / "storyboard.json")
    cfg_path = proj / "tutorial.config.json"
    cfg = load_json(cfg_path) if cfg_path.exists() else merge_config({}, {})
    asked = flags_to_config(args).get("saidas", [])
    if asked:  # pedido explícito: gera estas e as acrescenta ao registro de saídas do tutorial
        cfg["saidas"] = dedupe_outputs(cfg.get("saidas", []) + asked)
        cfg["canais"] = sorted(set(cfg.get("canais", [])) | set(parse_list(args.canal, CHANNELS)))
        cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    registered = {(s["formato"], s["resolucao"]): s for s in cfg.get("saidas", [])}
    targets = ([registered.get((s["formato"], s["resolucao"]), s) for s in asked] if asked
               else cfg.get("saidas") or [{"formato": cfg.get("format", "16:9"), "resolucao": "1080p"}])
    results = [export_one(proj, sb, cfg, s, args) for s in targets]
    print(f"{'arquivo':<44}{'dims':>11}{'modo':>13}{'legenda':>12}{'MB':>7}  texto da UI")
    for x in results:
        print(f"{x['arquivo']:<44}{x['dims']:>11}{x['modo']:>13}{x['legenda']:>12}{x['mb']:>7}  "
              f"{x['texto_ui_px']} px ({x['legibilidade']})" + (f"  [AVISO] {x['aviso']}" if x["aviso"] else ""))
        registrar(proj, f"saída {x['arquivo']} · {x['dims']} · modo {x['modo']} · legenda {x['legenda']}"
                  + (f" · canal {x['canal']}" if x["canal"] else "")
                  + f" · texto da UI ≈ {x['texto_ui_px']} px ({x['legibilidade']})" + (f" · {x['aviso']}" if x["aviso"] else ""))
    bad = [x for x in results if x["legibilidade"] == "ilegível"]
    if bad:
        print("\naviso: texto da interface ilegível em " + ", ".join(x["arquivo"] for x in bad)
              + ". Prefira uma resolução maior ou a adequação completa (composição nativa no formato).")
    return 0


# ---------------------------------------------------------------- composição

def cmd_render(args) -> int:
    """hyperframes render com TEMP local e novas tentativas.
    No Windows, frames e áudio intermediários em %TEMP%\\hf-render-* sumiram no meio do render (5 falhas
    seguidas); com TEMP/TMP apontando para renders/.tmp o render passou em todas as execuções."""
    proj = Path(args.project)
    sb = load_json(proj / "storyboard.json")
    cfg = project_config(proj)
    slug = sb["meta"].get("slug") or proj.name
    comp_dir = proj / (args.composicao or "composition")
    if args.composicao and not args.formato:
        die("--composicao exige --formato (ex.: --composicao composition-9x16 --formato 9:16)")
    name = f"{slug}-{fmt_key(args.formato)}.raw.mp4" if args.composicao else f"{slug}.raw.mp4"
    final_out = (proj / "renders" / name).resolve()
    final_out.parent.mkdir(parents=True, exist_ok=True)
    out = final_out
    # Windows: o hyperframes cria pastas temporárias ao lado da saída e estoura os 260 caracteres de caminho em
    # projetos fundos; nesse caso renderiza numa pasta curta e move o arquivo no fim
    if platform.system() == "Windows" and len(str(final_out)) > 110:
        import hashlib
        h = hashlib.sha1(str(final_out).encode()).hexdigest()[:10]
        out = Path.home() / ".hf-render" / h / f"{h}.mp4"   # uma pasta por projeto: renders em paralelo não se apagam
        out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.parent / ".tmp"
    tmp.mkdir(exist_ok=True)
    env = {**os.environ, "TEMP": str(tmp), "TMP": str(tmp), "TMPDIR": str(tmp)}
    quality = "draft" if (args.quality or cfg.get("quality")) == "rascunho" else "delivery"
    for attempt, workers in enumerate(("auto", "2", "1"), 1):
        out.unlink(missing_ok=True)
        cmd = ["npx", "--yes", "hyperframes", "render", "-o", str(out), "--fps", str(sb["meta"]["fps"]),
               "--quality", quality, "--workers", workers, "--video-frame-format", "png"]
        r = run(cmd, cwd=str(comp_dir), capture_output=True, text=True, env=env)
        if r.returncode == 0 and out.exists():
            shutil.rmtree(tmp, ignore_errors=True)
            if out != final_out:
                try:
                    shutil.move(str(out), str(final_out))
                    shutil.rmtree(out.parent, ignore_errors=True)
                except OSError as e:   # ex.: o MP4 de destino aberto num player
                    die(f"render pronto em {out}, mas não consegui mover para {final_out} ({e}); feche o arquivo e mova")
            print(f"{final_out} (tentativa {attempt}, workers {workers}, qualidade {quality})")
            return 0
        last = (r.stdout + r.stderr).strip().splitlines()[-3:]
        print(f"tentativa {attempt} falhou (workers {workers}): {' | '.join(last)[:300]}", file=sys.stderr)
    die("render falhou 3 vezes; rode com --debug no diretório composition/ para diagnóstico")
    return 1


def cmd_sfx(args) -> int:
    """Efeitos sonoros discretos gerados localmente (sem download, sem licença de terceiros)."""
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    recipes = {
        "click.wav": ["-f", "lavfi", "-i", "anoisesrc=d=0.04:c=white:a=0.6:seed=7",
                      "-af", "highpass=f=2200,lowpass=f=9000,afade=t=out:st=0.005:d=0.035,volume=0.7"],
        "pop.wav": ["-f", "lavfi", "-i", "aevalsrc='0.5*sin(2*PI*(520+900*exp(-28*t))*t)*exp(-14*t)':d=0.28:s=48000"],
        "whoosh.wav": ["-f", "lavfi", "-i", "anoisesrc=d=0.55:c=pink:a=0.5:seed=11",
                       "-af", "highpass=f=250,lowpass=f=3800,afade=t=in:d=0.3,afade=t=out:st=0.3:d=0.25,volume=0.45"],
        "tick.wav": ["-f", "lavfi", "-i", "aevalsrc='0.35*sin(2*PI*1800*t)*exp(-60*t)':d=0.08:s=48000"],
    }
    for name, rec in recipes.items():
        r = run(["ffmpeg", "-y", "-loglevel", "error", *rec, "-ar", "48000", "-ac", "1", str(out / name)],
                capture_output=True, text=True)
        if r.returncode != 0:
            die(f"falha ao gerar {name}: {r.stderr[-300:]}")
        print(out / name)
    return 0


def cmd_sync_composition(args) -> int:
    """Grava composition/timeline.js e ajusta data-start/data-duration de quem declara data-scene."""
    proj = Path(args.project)
    sb = load_json(proj / "storyboard.json")
    comp = proj / (args.composicao or "composition")
    scenes = {s["id"]: {"start": s["start"], "end": s["end"], "dur": round(s["end"] - s["start"], 3)} for s in sb["scenes"]}
    words = project_words(proj, sb)
    tl = {"duration": sb["meta"]["duration"], "scenes": scenes,
          "words": [{"t": round(w["start"], 3), "e": round(w["end"], 3), "w": w["text"]} for w in words]}
    (comp / "timeline.js").write_text("// gerado por tutorial.py sync-composition; não edite à mão\n"
                                      f"window.TL = {json.dumps(tl, ensure_ascii=False)};\n", encoding="utf-8")
    html_path = comp / args.html
    html = html_path.read_text(encoding="utf-8")
    total = sb["meta"]["duration"]

    def patch(m):
        tag, spec = m.group(0), m.group(1)
        if spec == "all":
            start, dur = 0.0, total
        else:
            a, _, b = spec.partition("-")
            if a not in scenes or (b and b not in scenes):
                die(f"data-scene=\"{spec}\" referencia cena inexistente")
            start, dur = scenes[a]["start"], round(scenes[b or a]["end"] - scenes[a]["start"], 3)
        off = re.search(r'data-offset="(-?[0-9.]+)"', tag)
        if off:  # efeito pontual dentro da cena (clique, whoosh): início deslocado, duração própria
            start = round(start + float(off.group(1)), 3)
        tag = re.sub(r'data-start="[^"]*"', f'data-start="{start}"', tag)
        if off or "data-keep-duration" in tag:
            return tag
        return re.sub(r'data-duration="[^"]*"', f'data-duration="{dur}"', tag)

    html, n = re.subn(r'<[^>]*\bdata-scene="([^"]+)"[^>]*>', patch, html)
    html_path.write_text(html, encoding="utf-8")
    print(f"timeline.js ({len(scenes)} cenas, {len(words)} palavras) + {n} elementos ajustados em {html_path.name}")
    return 0


# ---------------------------------------------------------------- design system e trava de marca

NEUTRALS = {"#FFFFFF", "#000000"}
GENERIC_FONTS = {"system-ui", "-apple-system", "sans-serif", "serif", "monospace", "inherit", "initial",
                 "blinkmacsystemfont", "segoe ui", "ui-sans-serif", "ui-monospace", "consolas", "cascadia code"}


def norm_hex(v: str) -> str | None:
    v = v.strip().lower()
    m = re.fullmatch(r"#([0-9a-f]{3}|[0-9a-f]{6})([0-9a-f]{2})?", v)
    if not m:
        return None
    h = m.group(1)
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return f"#{h.upper()}"


def rgb_to_hex(r, g, b) -> str:
    return f"#{int(float(r)):02X}{int(float(g)):02X}{int(float(b)):02X}"


def find_tokens(proj: Path) -> Path | None:
    for d in (proj, *proj.parents):
        for cand in (d / "design-tokens.json", d / "compartilhado" / "design-tokens.json"):
            if cand.exists():
                return cand
    return None


def cmd_design_tokens(args) -> int:
    """Normaliza a captura do hyperframes (extracted/tokens.json + design-styles.json + fonts-manifest.json)
    num design-tokens.json com origem de cada valor, e gera brand/brand.css com @font-face locais e variáveis."""
    cap = Path(args.capture)
    ext = cap / "extracted"
    tok = load_json(ext / "tokens.json")
    styles = load_json(ext / "design-styles.json") if (ext / "design-styles.json").exists() else {}
    fonts_m = load_json(ext / "fonts-manifest.json") if (ext / "fonts-manifest.json").exists() else {"files": []}
    out_dir = Path(args.out)
    brand = out_dir / "brand"
    (brand / "fonts").mkdir(parents=True, exist_ok=True)

    css_vars = tok.get("cssVariables", {})
    colors: dict[str, str] = {}
    for name, val in css_vars.items():
        hx = norm_hex(val)
        if hx:
            colors[name.lstrip("-").replace("color-", "")] = hx
    for b in styles.get("buttons", []):
        hx = norm_hex(b.get("background", ""))
        if hx and b.get("label") and b["label"] != "button":
            colors.setdefault(f"button:{b['label']}", hx)
    palette = sorted({*colors.values(), *(c for c in (norm_hex(x) for x in tok.get("colors", [])) if c)})

    def fam(var):
        return [f.strip().strip('"\'') for f in css_vars.get(var, "").split(",") if f.strip()][:1]

    fonts = {"heading": (fam("--font-heading") or [None])[0], "body": (fam("--font-body") or [None])[0]}
    if not fonts["heading"]:
        disp = next((t for t in styles.get("typography", []) if t.get("role") == "display"), None)
        fonts["heading"] = disp and disp["fontFamily"]
    families = sorted({f["family"] for f in tok.get("fonts", [])} | {v for v in fonts.values() if v})

    faces = []
    # 1º: as regras @font-face originais do site (preservam unicode-range e faixas de peso de fontes variáveis)
    page = ext / "page.html"
    html = page.read_text(encoding="utf-8", errors="ignore") if page.exists() else ""
    for block in re.findall(r"@font-face\s*{([^}]*)}", html):
        url = re.search(r"url\(\s*['\"]?([^'\")]+)", block)
        local = cap / "assets" / "fonts" / Path(url.group(1).split("?")[0]).name if url else None
        if not local or not local.exists():
            continue
        shutil.copyfile(local, brand / "fonts" / local.name)
        keep = [d.strip() for d in block.split(";") if d.strip() and not d.strip().startswith("src")]
        faces.append("@font-face { " + "; ".join(keep) + f"; src: url(\"fonts/{local.name}\") format(\"woff2\"); }}")
    # 2º: sem regras no HTML, monta pelo manifesto (sem unicode-range: um arquivo por família/peso)
    if not faces:
        seen = set()
        for f in fonts_m.get("files", []):
            key = (f["family"], f["weight"], f.get("style", "normal"))
            src = cap / "assets" / "fonts" / f["file"]
            if f.get("isIcon") or not f.get("identified") or key in seen or not src.exists():
                continue
            seen.add(key)
            shutil.copyfile(src, brand / "fonts" / f["file"])
            faces.append(f"@font-face {{ font-family: \"{f['family']}\"; font-weight: {f['weight']}; "
                         f"font-style: {key[2]}; src: url(\"fonts/{f['file']}\") format(\"woff2\"); }}")
    logo = None
    for a in (tok.get("sections") or [{}])[0].get("assets", []) or []:
        src = cap / a
        if src.exists():
            logo = brand / f"logo{src.suffix}"
            shutil.copyfile(src, logo)
            break
    radii = sorted({v for k, v in css_vars.items() if "radius" in k} | set(styles.get("radius", [])))

    tokens = {
        "source": {"capture": str(cap.resolve()), "title": tok.get("title"), "url_assets": (tok.get("sections") or [{}])[0].get("assetUrls")},
        "colors": colors, "palette": palette, "fonts": fonts, "font_families": families,
        "radii": radii, "shadows": {k: v for k, v in css_vars.items() if "shadow" in k},
        "logo": f"brand/{logo.name}" if logo else None,
    }
    (out_dir / "design-tokens.json").write_text(json.dumps(tokens, ensure_ascii=False, indent=2), encoding="utf-8")
    root_vars = "\n".join(f"  --brand-{k.replace(':', '-').replace(' ', '-').lower()}: {v};" for k, v in colors.items())
    font_vars = (f"  --brand-font-heading: \"{fonts['heading']}\", \"{fonts['body']}\", system-ui, sans-serif;\n"
                 f"  --brand-font-body: \"{fonts['body']}\", system-ui, sans-serif;")
    (brand / "brand.css").write_text(
        "/* gerado por tutorial.py design-tokens a partir do produto real; não edite à mão */\n"
        + "\n".join(faces) + f"\n:root {{\n{root_vars}\n{font_vars}\n}}\n", encoding="utf-8")
    print(f"{out_dir / 'design-tokens.json'}: {len(colors)} cores nomeadas, paleta {len(palette)}, "
          f"fontes {families}, {len(faces)} @font-face, logo {'ok' if logo else 'não encontrado'}")
    print(f"{brand / 'brand.css'} (importe na composição: <link rel=\"stylesheet\" href=\"brand/brand.css\">)")
    return 0


def audit_brand(proj: Path, rep: Report) -> None:
    """Trava de marca: cores e fontes da composição precisam vir do design-tokens.json do produto."""
    tpath = find_tokens(proj)
    if not tpath:
        rep.err("design-tokens.json não encontrado (rode: tutorial.py design-tokens <captura> --out <projeto>)")
        return
    tk = load_json(tpath)
    allowed = {c.upper() for c in tk["palette"]} | NEUTRALS
    cfg = project_config(proj).get("captions", {})
    if cfg.get("accent"):
        allowed.add(norm_hex(cfg["accent"]) or "")
    fams = {f.lower() for f in tk.get("font_families", [])} | GENERIC_FONTS
    files = [p for comp in sorted(proj.glob("composition*")) if comp.is_dir() for p in comp.rglob("*")
             if p.suffix in (".html", ".css") and "node_modules" not in p.parts and p.name != "brand.css"]
    for f in files:
        for n, line in enumerate(f.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            for m in re.finditer(r"#[0-9a-fA-F]{3,8}\b", line):
                hx = norm_hex(m.group(0)) if len(m.group(0)) in (4, 7, 9) else None
                if hx and hx not in allowed and not re.search(r"(href|src|url)\s*[=(][^)]*" + re.escape(m.group(0)), line):
                    rep.err(f"{f.name}:{n}: cor {m.group(0)} fora do design system")
            for m in re.finditer(r"rgba?\(\s*(\d+)[ ,]+(\d+)[ ,]+(\d+)", line):
                hx = rgb_to_hex(*m.groups())
                if hx not in allowed:
                    rep.err(f"{f.name}:{n}: cor {m.group(0)}) = {hx} fora do design system")
            for m in re.finditer(r"font-family\s*:\s*([^;{}]+)", line):
                for fam_name in [x.strip().strip('"\'') for x in m.group(1).split(",")]:
                    if fam_name and not fam_name.startswith("var(") and fam_name.lower() not in fams:
                        rep.err(f"{f.name}:{n}: fonte '{fam_name}' fora do design system")
    print(f"tokens: {tpath} · {len(files)} arquivo(s) verificados")


# ---------------------------------------------------------------- catálogo de tutoriais de um produto

CATALOG_STATUS = ("sugerido", "em-producao", "gerado", "desatualizado", "bloqueado")


def kebab(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def catalog_load(root: Path) -> dict:
    f = root / "catalogo.json"
    if not f.exists():
        die(f"{f} não existe (o agente cria o catálogo depois de mapear o produto; ver references/11-catalogo.md)")
    return load_json(f)


def catalog_save(root: Path, cat: dict) -> None:
    (root / "catalogo.json").write_text(json.dumps(cat, ensure_ascii=False, indent=2), encoding="utf-8")


def tutorial_dir(root: Path, t: dict) -> Path:
    """Pasta do tutorial: o campo 'pasta' do catálogo (relativo ao produto) ou <produto>/<slug>."""
    return root / t["pasta"] if t.get("pasta") else root / t["slug"]


def catalog_refresh(root: Path, cat: dict) -> None:
    """Status a partir do disco: render final presente = gerado (salvo bloqueado/desatualizado explícitos)."""
    for t in cat["tutoriais"]:
        mp4 = tutorial_dir(root, t) / "renders" / f"{t['slug']}.mp4"
        if mp4.exists() and t.get("status") not in ("bloqueado", "desatualizado"):
            t["status"] = "gerado"
        elif not mp4.exists() and t.get("status") == "gerado":
            t["status"] = "sugerido"


def catalog_queue(cat: dict) -> list[dict]:
    """Ordem do 'gerar todos': prioridade, depois observação antes de ação, depois a ordem do catálogo."""
    pend = [t for t in cat["tutoriais"] if t.get("status") in ("sugerido", "desatualizado", "em-producao")]
    return sorted(pend, key=lambda t: (t.get("prioridade", 3), t.get("tipo") == "acao", cat["tutoriais"].index(t)))


def cmd_catalog(args) -> int:
    root = Path(args.dir)
    cat = catalog_load(root)
    catalog_refresh(root, cat)
    if args.op == "add":
        if not args.titulo:
            die("--titulo é obrigatório")
        slug = args.slug or kebab(args.titulo)
        if any(t["slug"] == slug for t in cat["tutoriais"]):
            die(f"já existe um tutorial '{slug}' no catálogo")
        cat["tutoriais"].append({"slug": slug, "titulo": args.titulo, "perfil": args.perfil or "Todos",
                                 "jornada": args.jornada or args.perfil or "Outros", "objetivo": args.objetivo or "",
                                 "duracao_s": args.duracao or 45, "prioridade": args.prioridade or 2,
                                 "tipo": args.tipo or "observacao", "telas": [], "status": "sugerido",
                                 "notas": "adicionado a pedido do usuário"})
        print(f"adicionado: {slug}")
    elif args.op == "remove":
        before = len(cat["tutoriais"])
        cat["tutoriais"] = [t for t in cat["tutoriais"] if t["slug"] != args.slug]
        if len(cat["tutoriais"]) == before:
            die(f"'{args.slug}' não está no catálogo")
        print(f"removido do catálogo: {args.slug} (a pasta, se existir, não foi apagada)")
    elif args.op == "set":
        if not args.slug or args.status not in CATALOG_STATUS:
            die(f"use: catalog set <dir> --slug <slug> --status {'|'.join(CATALOG_STATUS)}")
        t = next((t for t in cat["tutoriais"] if t["slug"] == args.slug), None) or die(f"'{args.slug}' não está no catálogo")
        t["status"] = args.status
        print(f"{args.slug}: {args.status}")
    elif args.op == "next":
        q = catalog_queue(cat)
        catalog_save(root, cat)
        if not q:
            print("nada pendente: todos os tutoriais do catálogo estão gerados ou bloqueados")
            return 1
        t = q[0]
        print(json.dumps({"slug": t["slug"], "titulo": t["titulo"], "pasta": str(root / t["slug"]),
                          "tipo": t.get("tipo"), "requer": t.get("requer"), "restantes": len(q)}, ensure_ascii=False))
        return 0
    catalog_save(root, cat)
    for t in cat["tutoriais"]:  # saídas já geradas de cada tutorial (para a coluna "Saídas")
        renders = tutorial_dir(root, t) / "renders"
        t["_saidas"] = (["mestre"] if (renders / f"{t['slug']}.mp4").exists() else []) + sorted(
            p.stem.removeprefix(t["slug"] + "-").replace("x", ":", 1) for p in renders.glob(f"{t['slug']}-*-*p.mp4"))
    (root / "CATALOGO.md").write_text(render_catalog(cat), encoding="utf-8")
    counts = {s: sum(t.get("status") == s for t in cat["tutoriais"]) for s in CATALOG_STATUS}
    print(f"{root / 'CATALOGO.md'}: {len(cat['tutoriais'])} tutoriais · "
          + ", ".join(f"{k} {v}" for k, v in counts.items() if v))
    if cat.get("empresa"):
        # o produto faz parte da vitrine de uma empresa: refaz a vitrine e, se a publicação automática
        # estiver ligada (publicar <empresa> --auto on), envia; falha de rede não derruba o catálogo
        emp_root = (root / cat["empresa"]).resolve()
        vitrine_build(emp_root)
        if (empresa_load(emp_root).get("publicacao") or {}).get("automatica"):
            try:
                vitrine_publish(emp_root)
            except SystemExit as e:
                print(f"aviso: publicação automática não concluída ({e.code}); rode: tutorial.py publicar {emp_root}")
    return 0


def render_catalog(cat: dict) -> str:
    p = cat["produto"]
    icon = {"sugerido": "sugerido", "em-producao": "em produção", "gerado": "**gerado**",
            "desatualizado": "desatualizado", "bloqueado": "bloqueado"}
    out = [f"# Catálogo de tutoriais — {p['nome']}", "",
           f"- Produto: {p['url']}",
           f"- Design system: `{p.get('design_tokens', 'compartilhado/design-tokens.json')}` (todos os tutoriais usam a mesma marca)"]
    if p.get("pastas"):
        out.append(f"- Pastas: {p['pastas']}")
    if cat.get("empresa"):
        out.append(f"- Vitrine: `{cat['empresa']}/site/` (todos os aplicativos da empresa; `tutorial.py vitrine` / `publicar`)")
    out += [
           f"- Mapeado em: {p.get('mapeado_em', '?')} · método: {p.get('metodo', '')}",
           "- Gerado por `tutorial.py catalog render` a partir de `catalogo.json`; não edite este arquivo à mão."]
    pad = cat.get("padroes") or {}
    if pad:
        out.append("- Padrões do produto (valem para todo tutorial novo): "
                   + " · ".join(f"{k} {', '.join(v) if isinstance(v, list) else v}" for k, v in pad.items()))
    out.append("")
    if p.get("perfis"):
        out += ["## Perfis mapeados", "", "| Perfil | Tela inicial | Situação | Observações |", "|---|---|---|---|"]
        out += [f"| {x['nome']} | `{x.get('rota') or '—'}` | {x.get('status', '')} | {x.get('notas', '')} |" for x in p["perfis"]]
        out.append("")
    if cat.get("achados"):
        out += ["## Achados do mapeamento", ""] + [f"- {a}" for a in cat["achados"]] + [""]
    out += ["## Tutoriais", ""]
    jornadas = list(dict.fromkeys(t.get("jornada", "Outros") for t in cat["tutoriais"]))
    n = 0
    for j in jornadas:
        out += [f"### {j}", "", "| # | Tutorial | Pasta | Duração | Tipo | Status | Saídas | Comando |",
                "|---|---|---|---|---|---|---|---|"]
        for t in [t for t in cat["tutoriais"] if t.get("jornada", "Outros") == j]:
            n += 1
            tipo = ("observação" if t.get("tipo") == "observacao"
                    else f"ação<br><small>requer: {t.get('requer', 'autorização')}</small>")
            verbo = "regenerar" if t.get("status") == "gerado" else "gerar"
            cmd = "—" if t.get("status") == "bloqueado" else f"`/aidd-tutorial-creator {verbo} {t['slug']}`"
            obs = f"<br>{t['notas']}" if t.get("notas") else ""
            out.append(f"| {n} | {t['titulo']}<br><small>{t.get('objetivo', '')}</small>{obs} | `{t.get('pasta') or t['slug']}/` | "
                       f"{t.get('duracao_s', '?')} s | {tipo} | {icon.get(t.get('status'), t.get('status'))} | "
                       f"{'<br>'.join(t.get('_saidas') or []) or '—'} | {cmd} |")
        out.append("")
    q = catalog_queue(cat)
    out += ["## Gerar todos", "", "```text", "/aidd-tutorial-creator gerar todos", "```", "",
            "Ordem (prioridade, observação antes de ação):", ""]
    out += [f"{i}. `{t['slug']}`" + (f" — para antes e pede: {t['requer']}" if t.get("requer") else "") for i, t in enumerate(q, 1)]
    total = sum(t.get("duracao_s", 0) for t in q)
    out += ["", f"{len(q)} tutoriais pendentes, cerca de {total // 60} min {total % 60} s de vídeo no total.", "",
            "## Comandos do catálogo", "", "```text",
            f"/aidd-tutorial-creator catalogo {p['url']}     refaz a análise e mostra o que mudou",
            "/aidd-tutorial-creator gerar <pasta>                gera um tutorial",
            "/aidd-tutorial-creator gerar todos                  gera todos, um de cada vez, na ordem acima",
            "/aidd-tutorial-creator regenerar <pasta>            refaz um tutorial",
            "/aidd-tutorial-creator adicionar \"<fluxo>\"          inclui um tutorial novo no catálogo",
            "/aidd-tutorial-creator adequar <pasta> --formatos 9:16,1:1 --resolucoes 720p",
            "/aidd-tutorial-creator adequar <pasta> --canal instagram-reels,plataforma-ensino",
            "/aidd-tutorial-creator mudar legenda <pasta> --legenda bold-pop",
            "```", ""]
    return "\n".join(out)


# ---------------------------------------------------------------- vitrine da empresa (vários aplicativos)
#
# <empresa>/empresa.json lista os aplicativos (cada um com seu catalogo.json); `vitrine` monta <empresa>/site/
# (página única, vídeos, capas, prévias, manifest.json) e `publicar` envia à VPS só o que mudou. Tudo é script:
# nenhuma etapa depende do agente, então rodar de novo sem mudança nos vídeos não muda nenhum byte do site.

VITRINE_CORES = {  # o layout de streaming é escuro; primary/accent/night/muted/soft vêm dos design tokens
    "ink": "#000000", "night": "#0F172A", "slate": "#314158", "line": "#314158", "text": "#FFFFFF",
    "soft": "#CBD5E1", "muted": "#64748B", "primary": "#00568F", "primary-hover": "#004370",
    "accent": "#0284C7", "glow": "#74D4FF", "new": "#5EE9B5",
}
VITRINE_NOVO_DIAS = 14     # vídeo "novo" = render até 14 dias antes do mais recente do aplicativo
VITRINE_PROXIMO_S = 5      # contagem do próximo vídeo automático (empresa.json > vitrine.proximo_s; 0 desliga)
VITRINE_PREVIA_S = 8
MARCA_ARQUIVOS = ("logo.webp", "simbolo.png", "fontes.css")


def empresa_load(root: Path) -> dict:
    f = root / "empresa.json"
    if not f.exists():
        die(f"{f} não existe: crie com tutorial.py empresa init {root} --nome \"<empresa>\"")
    return load_json(f)


def empresa_save(root: Path, emp: dict) -> None:
    (root / "empresa.json").write_text(json.dumps(emp, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rel_posix(target: Path, start: Path) -> str:
    return Path(os.path.relpath(target.resolve(), start.resolve())).as_posix()


def file_sig(p: Path) -> list:
    st = p.stat()
    return [st.st_size, st.st_mtime_ns]


def sha256_cached(p: Path, cache: dict) -> str:
    import hashlib
    key = f"sha:{p.as_posix()}"
    if cache.get(key, {}).get("sig") == file_sig(p):
        return cache[key]["sha"]
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    cache[key] = {"sig": file_sig(p), "sha": h.hexdigest()}
    return cache[key]["sha"]


def vitrine_css(root: Path, emp: dict) -> str:
    cores, fontes = dict(VITRINE_CORES), {"heading": "Poppins", "body": "Inter"}
    tok_f = root / (emp.get("marca") or {}).get("tokens", "marca/design-tokens.json")
    if tok_f.exists():
        tok = load_json(tok_f)
        c = tok.get("colors") or {}
        for src, dst in (("primary", "primary"), ("primary-hover", "primary-hover"), ("accent", "accent"),
                         ("text", "night"), ("text-muted", "muted"), ("border-hover", "soft")):
            if c.get(src):
                cores[dst] = c[src]
        fontes.update({k: v for k, v in (tok.get("fonts") or {}).items() if v})
    cores.update(emp.get("cores") or {})
    lines = [f"    --{k}: {v};" for k, v in cores.items()]
    lines += [f'    --font-head: "{fontes["heading"]}", "{fontes["body"]}", system-ui, sans-serif;',
              f'    --font-body: "{fontes["body"]}", system-ui, sans-serif;', "    --radius: 8px;"]
    return "\n".join(lines)


def ffmpeg_out(cmd: list[str], out: Path) -> None:
    """Roda o ffmpeg gravando num temporário e só então troca o arquivo (nunca deixa saída pela metade)."""
    if not which("ffmpeg"):
        die("ffmpeg não encontrado (instale o ffmpeg)")
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(out.stem + ".tmp" + out.suffix)
    r = run(["ffmpeg", "-y", "-v", "error", *cmd, str(tmp)], capture_output=True, text=True)
    if r.returncode != 0 or not tmp.exists():
        tmp.unlink(missing_ok=True)
        die(f"ffmpeg falhou ao gerar {out.name}: {r.stderr.strip()[-400:]}")
    os.replace(tmp, out)


def vitrine_media(site: Path, rel: str, src: Path, params: list, cmd: list[str], cache: dict) -> None:
    """Gera site/<rel> a partir de src; refaz só se a fonte ou os parâmetros mudaram."""
    out = site / rel
    key = f"out:{rel}"
    want = {"src": file_sig(src), "params": params}
    if out.exists() and cache.get(key) == want:
        return
    ffmpeg_out(cmd, out)
    cache[key] = want
    print(f"  gerado {rel}")


def vitrine_stream(site: Path, pre: str, base: str, proj: Path, cache: dict) -> dict | None:
    """HLS do tutorial: uma faixa de vídeo (o render sem legenda) e uma faixa de áudio por idioma, como nos serviços
    de streaming; mais uma legenda .vtt por idioma. A pasta leva o hash das fontes, então nunca fica cache velho."""
    man_f = proj / "idiomas" / "idiomas.json"
    if not man_f.exists():
        return None
    man = load_json(man_f)
    raw = proj / man["video"]
    langs = [m for m in man["idiomas"] if (proj / "idiomas" / m["faixa"]).exists()]
    if not raw.exists() or not langs:
        return None
    # o nome da pasta depende só de imagem e áudio: corrigir uma legenda não reenvia o vídeo
    fontes = [raw] + [proj / "idiomas" / m["faixa"] for m in langs]
    h = short_hash(json.dumps([[f.name, file_sig(f)] for f in fontes] + [[m["idioma"], m["nome"]] for m in langs]))
    rel_dir = f"{pre}/stream/{base}-{h}"
    out = site / rel_dir
    hls = ["-f", "hls", "-hls_time", "6", "-hls_playlist_type", "vod", "-hls_segment_type", "fmp4",
           "-hls_flags", "independent_segments"]
    if not (out / "master.m3u8").exists():
        tmp = out.with_name(out.name + ".tmp")
        shutil.rmtree(tmp, ignore_errors=True)
        tmp.mkdir(parents=True)
        jobs = [(["-i", str(raw), "-an", "-c:v", "copy"], "v")]
        jobs += [(["-i", str(proj / "idiomas" / m["faixa"]), "-vn", "-c:a", "copy"], f"a_{m['idioma']}") for m in langs]
        for inp, name in jobs:
            r = run(["ffmpeg", "-y", "-v", "error", *inp, *hls, "-hls_fmp4_init_filename", f"{name}_init.mp4",
                     "-hls_segment_filename", f"{name}_%03d.m4s", f"{name}.m3u8"], cwd=str(tmp), capture_output=True, text=True)
            if r.returncode:
                shutil.rmtree(tmp, ignore_errors=True)
                die(f"HLS de {base} ({name}) falhou: {r.stderr[-300:]}")
        v = next(s for s in ffprobe(raw)["streams"] if s["codec_type"] == "video")
        prof = {"High": "6400", "Main": "4d00", "Constrained Baseline": "42e0", "Baseline": "42e0"}.get(v.get("profile"), "6400")
        codec = f"avc1.{prof}{int(v.get('level', 40)):02x}"
        bw = int(float(ffprobe(raw)["format"].get("bit_rate", 4_000_000))) + 160_000
        lines = ["#EXTM3U", "#EXT-X-VERSION:7", "#EXT-X-INDEPENDENT-SEGMENTS"]
        for i, m in enumerate(langs):
            lines.append(f'#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="aud",LANGUAGE="{m["idioma"]}",NAME="{m["nome"]}",'
                         f'DEFAULT={"YES" if i == 0 else "NO"},AUTOSELECT=YES,CHANNELS="2",URI="a_{m["idioma"]}.m3u8"')
        lines += [f'#EXT-X-STREAM-INF:BANDWIDTH={bw},RESOLUTION={v["width"]}x{v["height"]},CODECS="{codec},mp4a.40.2",AUDIO="aud"',
                  "v.m3u8", ""]
        (tmp / "master.m3u8").write_text("\n".join(lines), encoding="utf-8", newline="\n")
        if out.exists():
            shutil.rmtree(out)
        os.replace(tmp, out)
        print(f"  gerado {rel_dir}/ (HLS: vídeo + {len(langs)} faixa(s) de áudio)")
    idiomas = []
    for m in langs:   # legendas a cada montagem; o ?v= troca o endereço quando o texto muda
        src, dst = proj / "idiomas" / m["legenda"], out / f"leg_{m['idioma']}.vtt"
        if not dst.exists() or dst.read_bytes() != src.read_bytes():
            shutil.copyfile(src, dst)
        idiomas.append({"idioma": m["idioma"], "nome": m["nome"],
                        "legenda": f"{rel_dir}/{dst.name}?v={sha256_cached(dst, cache)[:10]}"})
    return {"rel_dir": rel_dir, "files": [f"{rel_dir}/{f.name}" for f in sorted(out.iterdir())],
            "stream": f"{rel_dir}/master.m3u8", "origem": man["origem"], "idiomas": idiomas}


def vitrine_build(root: Path) -> dict:
    """Monta <empresa>/site/ a partir do empresa.json e dos catálogos; devolve o manifest."""
    emp = empresa_load(root)
    site = root / "site"
    cache_f = root / ".vitrine-cache.json"
    cache = json.loads(cache_f.read_text(encoding="utf-8")) if cache_f.exists() else {}
    keep: set[str] = set()

    # marca da empresa: uma só para todos os aplicativos
    marca = root / (emp.get("marca") or {}).get("pasta", "marca")
    for name in MARCA_ARQUIVOS:
        if not (marca / name).exists():
            die(f"falta {marca / name} (a marca da empresa: {', '.join(MARCA_ARQUIVOS)} e fonts/)")
    for f in [marca / n for n in MARCA_ARQUIVOS] + sorted((marca / "fonts").glob("*")):
        rel = f"assets/marca/{rel_posix(f, marca)}"
        keep.add(rel)
        dst = site / rel
        if not dst.exists() or dst.read_bytes() != f.read_bytes():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(f, dst)

    apps, tuts, recentes = [], [], []
    usa_hls = False
    for a in emp.get("aplicativos") or []:
        aroot = (root / a["pasta"]).resolve()
        cat = catalog_load(aroot)
        catalog_refresh(aroot, cat)
        lista = [t for t in cat["tutoriais"] if t.get("status") != "bloqueado"]
        jornadas = [j for j in (cat.get("jornadas") or []) if any(t.get("jornada") == j for t in lista)]
        jornadas += [j for j in dict.fromkeys(t.get("jornada", "Outros") for t in lista) if j not in jornadas]
        apps.append({"slug": a["slug"], "nome": a["nome"], "descricao": a.get("descricao", ""),
                     "jornadas": jornadas, "legado": a.get("legado") or aroot.name})
        datas = []
        for i, t in enumerate(cat["tutoriais"], 1):
            if t.get("status") == "bloqueado":
                continue
            n = t.get("numero", i)
            item = {"id": f"{a['slug']}/{t['slug']}", "app": a["slug"], "slug": t["slug"], "numero": n,
                    "titulo": t["titulo"], "objetivo": t.get("objetivo", ""), "jornada": t.get("jornada", "Outros"),
                    "perfil": t.get("perfil", "Todos"), "video": None}
            renders = tutorial_dir(aroot, t) / "renders"
            final = renders / f"{t['slug']}.mp4"
            # só entra pronto: com vários idiomas configurados, o tutorial espera idiomas.json (senão iria ao ar
            # pela metade, só em português, no meio da produção) e aparece como "em breve"
            pedidos = project_config(tutorial_dir(aroot, t)).get("idiomas") or IDIOMAS_PADRAO
            falta_idioma = len(pedidos) > 1 and not (tutorial_dir(aroot, t) / "idiomas" / "idiomas.json").exists()
            if falta_idioma and final.exists():
                print(f"  {a['slug']}/{t['slug']}: aguardando idiomas ({', '.join(pedidos)}); fica como 'em breve'")
            if t.get("status") in ("gerado", "desatualizado") and final.exists() and not falta_idioma:
                limpo = renders / f"{t['slug']}.raw.mp4"   # sem legenda queimada: melhor para capa e prévia
                limpo = limpo if limpo.exists() else final
                dkey = f"dur:{final.as_posix()}"
                if cache.get(dkey, {}).get("sig") != file_sig(final):
                    cache[dkey] = {"sig": file_sig(final), "dur": round(media_duration(final), 1)}
                dur = cache[dkey]["dur"]
                capa = float(t.get("capa_s", round(dur * 0.4, 2)))
                previa = float(t.get("previa_s", round(dur * 0.25, 2)))
                base, pre = f"{n:02d}-{t['slug']}", f"apps/{a['slug']}"
                # com idiomas: HLS (imagem sem legenda + áudio e legenda por idioma) e nenhum mp4 duplicado;
                # sem idiomas: o mp4 final com a legenda queimada, como sempre
                st = vitrine_stream(site, pre, base, tutorial_dir(aroot, t), cache)
                rels = {"poster": f"{pre}/capas/{base}.jpg", "hero": f"{pre}/capas/{base}-hero.jpg",
                        "preview": f"{pre}/previas/{base}.mp4"}
                if not st:
                    rels["video"] = f"{pre}/videos/{base}.mp4"
                    vitrine_media(site, rels["video"], final, [], ["-i", str(final), "-c", "copy", "-movflags", "+faststart"], cache)
                vitrine_media(site, rels["poster"], limpo, [capa, 640],
                              ["-ss", f"{capa}", "-i", str(limpo), "-frames:v", "1", "-vf", "scale=640:-2", "-q:v", "3"], cache)
                vitrine_media(site, rels["hero"], limpo, [capa, 1920],
                              ["-ss", f"{capa}", "-i", str(limpo), "-frames:v", "1", "-vf", "scale=1920:-2", "-q:v", "3"], cache)
                vitrine_media(site, rels["preview"], limpo, [previa, VITRINE_PREVIA_S],
                              ["-ss", f"{previa}", "-t", str(VITRINE_PREVIA_S), "-i", str(limpo), "-an",
                               "-vf", "scale=640:-2,fps=24", "-c:v", "libx264", "-preset", "slow", "-crf", "30",
                               "-pix_fmt", "yuv420p", "-movflags", "+faststart"], cache)
                srt = renders / f"{t['slug']}.srt"
                if srt.exists() and not st:
                    rels["legenda"] = f"{pre}/videos/{base}.srt"
                    dst = site / rels["legenda"]
                    if not dst.exists() or dst.read_bytes() != srt.read_bytes():
                        shutil.copyfile(srt, dst)
                keep.update(rels.values())
                # ?v=<hash>: o nginx guarda mídia por 7 dias; vídeo refeito com o mesmo nome muda o endereço
                for k, rel in rels.items():
                    item[k] = f"{rel}?v={sha256_cached(site / rel, cache)[:10]}"
                if st:
                    keep.update(st["files"])
                    item["video"] = item["stream"] = st["stream"]
                    item["origem"], item["idiomas"] = st["origem"], st["idiomas"]
                    usa_hls = True
                item["duracao"] = dur
                item["_data"] = final.stat().st_mtime
                datas.append(item["_data"])
            tuts.append(item)
        if datas:
            recentes.append(max(datas))
            corte = max(datas) - VITRINE_NOVO_DIAS * 86400
            for item in tuts:
                if item["app"] == a["slug"] and item.get("_data"):
                    item["novo"] = item["_data"] >= corte
    for item in tuts:
        item.pop("_data", None)
    if usa_hls:  # player de streaming servido junto com o site (sem CDN em tempo de uso)
        rel = "assets/js/hls.min.js"
        keep.add(rel)
        src, dst = TEMPLATES / "vendor" / "hls.min.js", site / rel
        if not dst.exists() or dst.read_bytes() != src.read_bytes():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)

    # o que sobrou no site e não pertence a esta montagem sai (o site é inteiro derivado)
    for f in sorted(site.rglob("*")) if site.exists() else []:
        rel = f.relative_to(site).as_posix()
        if f.is_file() and rel not in keep and rel not in ("index.html", "manifest.json"):
            f.unlink()
    for d in sorted((p for p in site.rglob("*") if p.is_dir()), key=lambda p: -len(p.parts)):
        if not any(d.iterdir()):
            d.rmdir()

    import datetime as _dt
    nome = emp["empresa"]["nome"]
    atualizado = _dt.datetime.fromtimestamp(max(recentes)).strftime("%d/%m/%Y") if recentes else "—"
    vit = emp.get("vitrine") or {}
    data = {"empresa": nome, "empresa_slug": emp["empresa"].get("slug") or kebab(nome),
            "proximo_s": vit.get("proximo_s", VITRINE_PROXIMO_S), "aplicativos": apps, "tutoriais": tuts}
    html = (TEMPLATES / "vitrine.html").read_text(encoding="utf-8")
    titulo = f"Tutoriais {nome}" if len(apps) != 1 else f"Tutoriais {apps[0]['nome']}"
    for k, v in {"TITULO": escape_html(titulo), "DESCRICAO": escape_html(f"Tutoriais em vídeo de {nome}"),
                 "EMPRESA": escape_html(nome), "ATUALIZADO": atualizado, "CORES": vitrine_css(root, emp),
                 "DATA": json.dumps(data, ensure_ascii=False).replace("</", "<\\/")}.items():
        html = html.replace("{{" + k + "}}", v)
    site.mkdir(parents=True, exist_ok=True)
    idx = site / "index.html"
    if not idx.exists() or idx.read_text(encoding="utf-8") != html:
        idx.write_text(html, encoding="utf-8", newline="\n")

    arquivos = {}
    for f in sorted(site.rglob("*")):
        rel = f.relative_to(site).as_posix()
        if f.is_file() and rel != "manifest.json":
            arquivos[rel] = {"sha256": sha256_cached(f, cache), "bytes": f.stat().st_size}
    import hashlib
    versao = hashlib.sha256(json.dumps(arquivos, sort_keys=True).encode()).hexdigest()[:16]
    manifest = {"empresa": nome, "versao": versao, "arquivos": arquivos}
    (site / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    cache = {k: v for k, v in cache.items() if not k.startswith("sha:") or Path(k[4:]).exists()}
    cache_f.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    prontos = sum(1 for t in tuts if t["video"])
    total = sum(m["bytes"] for m in arquivos.values())
    print(f"{site}: {len(apps)} aplicativo(s) · {prontos} vídeo(s) · {len(tuts) - prontos} em breve · "
          f"{total / 1e6:.1f} MB · versão {versao}")
    return manifest


def escape_html(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def ssh_run(host: str, remote_cmd: str, **kw) -> subprocess.CompletedProcess:
    # BatchMode: sem chave aceita o ssh falha em vez de esperar senha (a publicação automática roda sem ninguém olhando)
    return run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", host, remote_cmd], **kw)


def ssh_pipe(host: str, remote_cmd: str) -> subprocess.Popen:
    """ssh com a entrada aberta: o tar dos arquivos vai direto para o servidor, sem rsync nem arquivo temporário."""
    return subprocess.Popen([which("ssh") or "ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", host, remote_cmd],
                            stdin=subprocess.PIPE)


def vitrine_publish(root: Path, dry: bool = False, limpar: bool = False, forcar: bool = False) -> int:
    """Envia <empresa>/site/ para a VPS: só arquivos novos ou mudados, index.html por último."""
    import shlex
    import tarfile
    emp = empresa_load(root)
    pub = emp.get("publicacao") or die("empresa.json sem 'publicacao' (ssh, pasta_vps, dominio)")
    host, dest = pub["ssh"], pub["pasta_vps"].rstrip("/")
    site = root / "site"
    local = load_json(site / "manifest.json")
    last_f = root / ".publicado.json"
    if not (forcar or limpar or dry) and last_f.exists() and load_json(last_f).get("versao") == local["versao"]:
        print(f"nada a publicar: a versão {local['versao']} já está no ar")
        return 0
    r = ssh_run(host, f"cat {shlex.quote(dest + '/manifest.json')} 2>/dev/null || true", capture_output=True, text=True)
    if r.returncode != 0:
        die(f"ssh {host} falhou: {r.stderr.strip() or 'sem resposta'}")
    try:
        remote = json.loads(r.stdout) if r.stdout.strip() else {}
    except json.JSONDecodeError:
        remote = {}
    rfiles = remote.get("arquivos") or {}
    mudou = [p for p, m in local["arquivos"].items() if forcar or (rfiles.get(p) or {}).get("sha256") != m["sha256"]]
    sair = [p for p in rfiles if p not in local["arquivos"]]
    if limpar:  # primeira vez num servidor com arquivos de outra montagem: apaga o que o manifest não conhece
        r = ssh_run(host, f"cd {shlex.quote(dest)} 2>/dev/null && find . -type f", capture_output=True, text=True)
        sair = sorted({p.removeprefix("./") for p in r.stdout.split()} - set(local["arquivos"]) - {"manifest.json"})
    for p in mudou + sair:
        if p.startswith("/") or ".." in p.split("/"):
            die(f"caminho inválido no manifest: {p}")
    if not mudou and not sair and remote.get("versao") == local["versao"]:
        last_f.write_text(json.dumps({"versao": local["versao"]}) + "\n", encoding="utf-8")
        print(f"nada a publicar: a versão {local['versao']} já está no ar")
        return 0
    envio = sum(local["arquivos"][p]["bytes"] for p in mudou)
    print(f"publicar em {host}:{dest} → {len(mudou)} arquivo(s) ({envio / 1e6:.1f} MB), {len(sair)} a remover")
    for p in mudou[:20] + [f"- {p}" for p in sair[:20]]:
        print(f"  {p}")
    if dry:
        print("(simulação: nada foi enviado)")
        return 0

    def send(paths: list[str]) -> None:
        if not paths:
            return
        proc = ssh_pipe(host, f"mkdir -p {shlex.quote(dest)} && tar -xf - -C {shlex.quote(dest)}")
        with tarfile.open(fileobj=proc.stdin, mode="w|") as tar:
            for p in paths:
                info = tar.gettarinfo(str(site / p), arcname=p)
                info.uid = info.gid = 0
                info.uname = info.gname = "root"
                info.mode = 0o644
                with (site / p).open("rb") as fh:
                    tar.addfile(info, fh)
        proc.stdin.close()
        if proc.wait() != 0:
            die(f"envio para {host} falhou (código {proc.returncode})")

    # mídia primeiro, depois a página e o manifest, e só então o que saiu: ninguém vê a página nova apontando
    # para vídeo que não chegou, nem a antiga apontando para vídeo já apagado
    send([p for p in mudou if p != "index.html"])
    send([p for p in mudou if p == "index.html"] + ["manifest.json"])
    if sair:   # a lista vai pela entrada do ssh (centenas de caminhos estouram a linha de comando do Windows)
        r = ssh_run(host, f"cd {shlex.quote(dest)} && xargs -0 rm -f -- && find . -mindepth 1 -type d -empty -delete",
                    input="\0".join(sair), capture_output=True, text=True)
        if r.returncode:
            print(f"aviso: não removi {len(sair)} arquivo(s) antigos ({r.stderr.strip()[-200:]}); rode publicar --limpar")

    ok = None
    if pub.get("dominio"):
        import time
        import urllib.request
        try:
            with urllib.request.urlopen(f"https://{pub['dominio']}/manifest.json?t={int(time.time())}", timeout=20) as resp:
                ok = json.loads(resp.read().decode("utf-8")).get("versao") == local["versao"]
        except Exception as e:  # sem rede para conferir não invalida o envio, que já terminou
            print(f"aviso: não consegui conferir https://{pub['dominio']} ({e})")
    last_f.write_text(json.dumps({"versao": local["versao"]}) + "\n", encoding="utf-8")
    if ok is False:
        die(f"enviado, mas https://{pub['dominio']} ainda mostra outra versão (cache ou pasta errada?)")
    print(f"[OK] no ar{' e conferido' if ok else ''}: https://{pub.get('dominio', host)} (versão {local['versao']})")
    return 0


def cmd_vitrine(args) -> int:
    root = Path(args.dir)
    vitrine_build(root)
    if args.publicar:
        return vitrine_publish(root)
    return 0


def cmd_publicar(args) -> int:
    root = Path(args.dir)
    emp = empresa_load(root)
    if args.auto:
        emp.setdefault("publicacao", {})["automatica"] = args.auto == "on"
        empresa_save(root, emp)
        print("publicação automática " + ("LIGADA: todo 'catalog render' de um aplicativo da empresa refaz a vitrine e envia"
                                          if args.auto == "on" else "desligada: envie com tutorial.py publicar " + str(root)))
        return 0
    if not args.sem_gerar:
        vitrine_build(root)
    return vitrine_publish(root, dry=args.dry_run, limpar=args.limpar, forcar=args.forcar)


def cmd_empresa(args) -> int:
    root = Path(args.dir)
    if args.op == "init":
        if (root / "empresa.json").exists():
            die(f"{root / 'empresa.json'} já existe")
        if not args.nome:
            die("--nome é obrigatório")
        root.mkdir(parents=True, exist_ok=True)
        (root / "marca" / "fonts").mkdir(parents=True, exist_ok=True)
        empresa_save(root, {"empresa": {"nome": args.nome, "slug": args.slug or kebab(args.nome)},
                            "marca": {"pasta": "marca", "tokens": "marca/design-tokens.json"},
                            "vitrine": {"proximo_s": VITRINE_PROXIMO_S}, "aplicativos": [],
                            "publicacao": {"dominio": "", "ssh": "", "pasta_vps": "", "automatica": False}})
        print(f"criado {root / 'empresa.json'}; ponha em {root / 'marca'}: {', '.join(MARCA_ARQUIVOS)}, fonts/ e design-tokens.json")
        return 0
    emp = empresa_load(root)
    apps = emp.setdefault("aplicativos", [])
    if args.op == "add-app":
        if not args.pasta:
            die("--pasta é obrigatório (a pasta do aplicativo, com catalogo.json)")
        aroot = Path(args.pasta)
        cat = catalog_load(aroot)
        nome = args.nome or cat["produto"]["nome"]
        slug = args.slug or kebab(nome)
        if any(a["slug"] == slug for a in apps):
            die(f"já existe um aplicativo '{slug}' na empresa")
        apps.append({"slug": slug, "nome": nome, "pasta": rel_posix(aroot, root), "descricao": args.descricao or ""})
        cat["empresa"] = rel_posix(root, aroot)
        catalog_save(aroot, cat)
        print(f"aplicativo adicionado: {slug} ({nome})")
    elif args.op == "remove-app":
        a = next((a for a in apps if a["slug"] == args.slug), None) or die(f"'{args.slug}' não está na empresa")
        apps.remove(a)
        aroot = (root / a["pasta"]).resolve()
        if (aroot / "catalogo.json").exists():
            cat = catalog_load(aroot)
            cat.pop("empresa", None)
            catalog_save(aroot, cat)
        print(f"aplicativo removido da vitrine: {args.slug} (a pasta não foi apagada)")
    elif args.op == "list":
        pub = emp.get("publicacao") or {}
        print(f"{emp['empresa']['nome']} · {len(apps)} aplicativo(s) · publicação "
              f"{'automática' if pub.get('automatica') else 'manual'} em {pub.get('dominio') or '(sem domínio)'}")
        for a in apps:
            cat = catalog_load((root / a["pasta"]).resolve())
            catalog_refresh((root / a["pasta"]).resolve(), cat)
            g = sum(t.get("status") == "gerado" for t in cat["tutoriais"])
            print(f"  {a['slug']:<20} {a['nome']} · {g}/{len(cat['tutoriais'])} gerados · {a['pasta']}")
        return 0
    empresa_save(root, emp)
    return 0


# ---------------------------------------------------------------- REA

def cmd_extract_rea(args) -> int:
    data = load_json(Path(args.result))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    saved = []

    def walk(node, label: str, key: str):
        # label = step_id mais próximo acima; key = último nome de campo
        if isinstance(node, dict):
            label = str(node.get("step_id") or label)
            for k, v in node.items():
                walk(v, label, k)
        elif isinstance(node, list):
            for v in node:
                walk(v, label, key)
        elif isinstance(node, str):
            s = node.split(",", 1)[1] if node.startswith("data:image/png;base64,") else node
            if s.startswith(PNG_MAGIC_B64) and len(s) > 200:
                name = re.sub(r"[^A-Za-z0-9_.-]+", "_", label or key).strip("_") or "image"
                dst = out / f"{name}.png"
                n = 2
                while dst.exists():
                    dst = out / f"{name}-{n}.png"
                    n += 1
                dst.write_bytes(base64.b64decode(s))
                saved.append(dst)

    walk(data, "", "image")
    for p in saved:
        print(p)
    print(f"{len(saved)} imagens extraídas")
    return 0 if saved else 1


# ---------------------------------------------------------------- auditoria

class Report:
    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def err(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)

    def print(self, title):
        print(f"== {title}")
        for e in self.errors:
            print(f"ERRO  {e}")
        for w in self.warnings:
            print(f"AVISO {w}")
        status = "PASSOU" if not self.errors else "FALHOU"
        print(f"{status}: {len(self.errors)} erro(s), {len(self.warnings)} aviso(s)")
        return 0 if not self.errors else 1


def audit_storyboard(proj: Path, rep: Report) -> dict | None:
    sb_path = proj / "storyboard.json"
    if not sb_path.exists():
        rep.err("storyboard.json ausente")
        return None
    sb = load_json(sb_path)
    meta, scenes = sb.get("meta", {}), sb.get("scenes", [])
    for k in ("width", "height", "fps", "duration"):
        if k not in meta:
            rep.err(f"meta.{k} ausente")
    if not scenes:
        rep.err("nenhuma cena")
        return sb
    wps = float(meta.get("wps", 2.5))
    ids = [s.get("id") for s in scenes]
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        rep.err(f"ids de cena duplicados: {sorted(dup)}")
    prev_end, run_layout, run_len = 0.0, None, 0
    for i, sc in enumerate(scenes):
        sid = sc.get("id", f"#{i}")
        missing = [f for f in REQUIRED_SCENE_FIELDS if f not in sc]
        if missing:
            rep.err(f"{sid}: campos ausentes {missing}")
            continue
        start, end = float(sc["start"]), float(sc["end"])
        if i == 0 and abs(start) > CONTIGUITY_TOL:
            rep.err(f"{sid}: primeira cena começa em {start}, não em 0")
        if i > 0 and abs(start - prev_end) > CONTIGUITY_TOL:
            rep.err(f"{sid}: começa em {start:.2f}, mas a anterior termina em {prev_end:.2f}")
        if end - start < MIN_SCENE:
            rep.err(f"{sid}: duração {end - start:.2f} s < mínimo {MIN_SCENE} s")
        prev_end = end
        if sc["layout"] not in LAYOUTS:
            rep.err(f"{sid}: layout '{sc['layout']}' fora do menu {sorted(LAYOUTS)}")
        run_len = run_len + 1 if sc["layout"] == run_layout else 1
        run_layout = sc["layout"]
        if run_len > 2:
            rep.warn(f"{sid}: layout '{run_layout}' repetido {run_len} vezes seguidas")
        n = len(words(sc["narration"]))
        cap = (end - start) * wps * 1.1
        if n > cap:
            rep.err(f"{sid}: narração com {n} palavras não cabe em {end - start:.1f} s (máx. {cap:.0f} a {wps} p/s)")
        texts = sc.get("on_screen_text", [])
        if len(texts) > MAX_TEXT_ITEMS:
            rep.err(f"{sid}: {len(texts)} textos na tela (máx. {MAX_TEXT_ITEMS})")
        for t in texts:
            if len(words(t)) > MAX_TEXT_WORDS:
                rep.err(f"{sid}: texto na tela longo demais ({len(words(t))} palavras): “{t}”")
        audio = sc.get("audio")
        if audio and not (proj / audio).exists():
            rep.warn(f"{sid}: áudio {audio} ainda não existe")
        for key in ("keyframe_in", "keyframe_out"):
            if sc.get(key) and not (proj / sc[key]).exists():
                rep.warn(f"{sid}: {key} {sc[key]} ainda não existe")
    if "duration" in meta and abs(prev_end - float(meta["duration"])) > CONTIGUITY_TOL:
        rep.err(f"última cena termina em {prev_end:.2f}, meta.duration = {meta['duration']}")
    sm_path = proj / "step-map.json"
    if sm_path.exists():
        steps = load_json(sm_path).get("steps", [])
        used: dict[str, list[str]] = {}
        for sc in scenes:
            for st in sc.get("steps", []):
                used.setdefault(st, []).append(sc.get("id"))
        known = {s["id"] for s in steps}
        for s in steps:
            if s.get("excluded"):
                continue
            where = used.get(s["id"], [])
            if not where:
                rep.err(f"passo {s['id']} ({s.get('title', '')}) não aparece em nenhuma cena")
            elif len(where) > 1:
                rep.err(f"passo {s['id']} aparece em mais de uma cena: {where}")
            ev = s.get("evidence")
            if not ev or ev == "unknown":
                rep.err(f"passo {s['id']} sem evidência")
            elif not ev.startswith("static:") and not (proj / ev).exists():
                rep.err(f"passo {s['id']}: evidência {ev} não encontrada")
            before = s.get("evidence_before")
            if before and not (proj / before).exists():
                rep.err(f"passo {s['id']}: evidence_before {before} não encontrada")
        for st in used:
            if st not in known:
                rep.err(f"cena referencia passo inexistente: {st}")
    else:
        rep.warn("step-map.json ausente: cobertura de passos não verificada")
    return sb


def audit_final(proj: Path, rep: Report, render: Path | None) -> None:
    sb = audit_storyboard(proj, rep)
    if sb is None:
        return
    audit_captions(proj, rep)
    meta = sb["meta"]
    if render is None:  # o vídeo principal é renders/<slug>.mp4; saídas <slug>-<formato>-<res>.mp4 são auditadas à parte
        main = proj / "renders" / f"{sb['meta'].get('slug') or proj.name}.mp4"
        cands = [main] if main.exists() else sorted(
            (p for p in (proj / "renders").glob("*.mp4")
             if not p.name.endswith(".raw.mp4") and not re.search(r"-\d+x\d+-\d+p\.mp4$", p.name)),
            key=lambda p: p.stat().st_mtime, reverse=True)
        render = cands[0] if cands else None
    if render is None or not render.exists():
        rep.err("nenhum render .mp4 em renders/")
        return
    info = ffprobe(render)
    dur = float(info["format"]["duration"])
    if abs(dur - float(meta["duration"])) > DURATION_TOL:
        rep.err(f"render dura {dur:.2f} s; storyboard prevê {meta['duration']} s")
    video = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    audio = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    if not video:
        rep.err("render sem faixa de vídeo")
    else:
        if (video["width"], video["height"]) != (meta["width"], meta["height"]):
            rep.err(f"resolução {video['width']}x{video['height']} ≠ {meta['width']}x{meta['height']}")
        num, den = (video.get("avg_frame_rate") or "0/1").split("/")
        fps = float(num) / float(den or 1) if float(den or 1) else 0
        if abs(fps - float(meta["fps"])) > 0.5:
            rep.err(f"fps {fps:.2f} ≠ {meta['fps']}")
    has_narration = any(sc.get("narration") for sc in sb["scenes"])
    if has_narration and not audio:
        rep.err("há narração no storyboard, mas o render não tem faixa de áudio")
    slug = sb["meta"].get("slug") or proj.name
    for s in project_config(proj).get("saidas", []):
        f = proj / "renders" / f"{slug}-{fmt_key(s['formato'])}-{s['resolucao']}.mp4"
        if not f.exists():
            rep.err(f"saída registrada não gerada: {f.name} (rode: tutorial.py export {proj})")
            continue
        vs = next((x for x in ffprobe(f)["streams"] if x["codec_type"] == "video"), {})
        if f"{vs.get('width')}x{vs.get('height')}" != "x".join(map(str, output_dims(s["formato"], s["resolucao"]))):
            rep.err(f"{f.name}: dimensões {vs.get('width')}x{vs.get('height')} diferentes do pedido")
        if not f.with_suffix(".srt").exists():
            rep.warn(f"{f.name}: sem .srt ao lado")
    cap_style = project_config(proj).get("captions", {}).get("style")
    if cap_style and cap_style != "none" and not render.with_suffix(".ass").exists():
        rep.err(f"flag --legenda {cap_style} pede legenda queimada, mas {render.with_suffix('.ass').name} não existe "
                f"(rode: tutorial.py burn {proj})")
    srt = render.with_suffix(".srt")
    if not srt.exists():
        rep.err(f"legenda {srt.name} ausente")
    else:
        cues = parse_srt(srt)
        if not cues:
            rep.err(f"{srt.name} sem cues")
        else:
            if cues[-1][1] > dur + DURATION_TOL:
                rep.err(f"{srt.name} termina em {cues[-1][1]:.2f} s, depois do vídeo ({dur:.2f} s)")
            bounds = [float(sc["end"]) for sc in sb["scenes"][:-1]]
            for c0, c1, text in cues:
                if any(c0 < b - 0.05 and c1 > b + 0.3 for b in bounds):
                    rep.err(f"{srt.name}: bloco atravessa a troca de cena ({c0:.2f}–{c1:.2f} s): “{text}”")
            n_srt = len(words(" ".join(c[2] for c in cues)))
            n_script = len(words(" ".join(sc.get("narration", "") for sc in sb["scenes"])))
            if n_script and n_srt < 0.8 * n_script:
                rep.warn(f"{srt.name} tem {n_srt} palavras; narração tem {n_script} (cobertura < 80 %)")
    print(f"render: {render} ({dur:.2f} s)")


def sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?…])\s+", text) if len(words(s)) >= 3]


def audit_captions(proj: Path, rep: Report) -> None:
    """Colisão legenda × foco do passo, sem render: refaz a mesma decisão do `burn`/`export` (mesmos blocos,
    mesma geometria) para o mestre e para cada saída do tutorial.config.json, e reprova todo bloco cujo
    retângulo cobre um `target_box` (com zoom) ou uma `focus_boxes` da cena."""
    sb_path = proj / "storyboard.json"
    if not sb_path.exists():
        rep.err("storyboard.json ausente")
        return
    sb = load_json(sb_path)
    cfg = project_config(proj)
    cap = cfg.get("captions", {})
    W, H = int(sb["meta"]["width"]), int(sb["meta"]["height"])
    ws = project_words(proj, sb)
    if not ws:
        rep.warn("sem audio/*.words.json: blocos de legenda ainda não existem (rode tts antes)")
        return
    steps = {s["id"]: s for s in (load_json(proj / "step-map.json").get("steps", [])
                                  if (proj / "step-map.json").exists() else [])}
    for sc in sb.get("scenes", []):
        sem_alvo = [st for st in sc.get("steps", []) if not steps.get(st, {}).get("target_box")]
        if sem_alvo:
            rep.warn(f"{sc['id']}: passo(s) {sem_alvo} sem target_box: a legenda não pode ser checada contra o foco")
    slug = sb["meta"].get("slug") or proj.name
    alvos = [("mestre", cap.get("style"), W, H, project_focus_boxes(proj, sb), cap.get("size", "m"), None, None)]
    for saida in cfg.get("saidas", []):
        fmt, res = saida["formato"], saida["resolucao"]
        oW, oH = output_dims(fmt, res)
        native = (proj / "renders" / f"{slug}-{fmt_key(fmt)}.raw.mp4").exists()
        mode = "nativo" if native else "escalar" if abs(W / H - oW / oH) < 0.01 else "reenquadrar"
        top_f, base_f = saida.get("seguro_topo", 0.0), saida.get("seguro_base", 0.0)
        g = output_geometry(W, H, oW, oH, mode, top_f, base_f)
        if mode == "nativo" and not any(sc.get(f"focus_boxes_{fmt_key(fmt)}") for sc in sb.get("scenes", [])):
            rep.warn(f"saída {fmt} {res} (nativo): sem focus_boxes_{fmt_key(fmt)} nas cenas; colisão não verificada")
        mb, mt = safe_margins(oH, top_f, base_f)
        alvos.append((f"{fmt} {res}" + (f" ({saida['canal']})" if saida.get("canal") else ""),
                      saida.get("legenda") or cap.get("style"), oW, oH, output_focus_boxes(proj, sb, mode, g, fmt),
                      saida.get("tamanho") or cap.get("size", "m"), mb, mt))
    position, case, scene_pos = cap.get("position", "auto"), cap.get("case", "normal"), scene_caption_positions(sb)
    for nome, style, w, h, focus, size_key, mb, mt in alvos:
        style = style or ("bold-pop" if h > w else "highlight")
        if style in ("none", "nenhuma"):
            continue
        max_words = {"bold-pop": 3, "highlight": 5, "word-by-word": 6}.get(style, 7)
        cues = group_cues(ws, max_words, 2.6 if style == "bold-pop" else 3.4)
        placed = place_captions(cues, style, w, h, position, size_key, case, focus, scene_pos, mb, mt)
        for c in placed:
            r = c["rect"]
            if r[1] < 0 or r[1] + r[3] > h:
                rep.err(f"{nome} {c['scene']} {c['start']:.2f}s: legenda sai do quadro ({r}): “{c['text']}”")
            for hit in c["collisions"]:
                rep.err(f"{nome} {c['scene']} {c['start']:.2f}s: legenda ({c['position']}) cobre {hit['src']} "
                        f"{hit['box']}: “{c['text']}”" + ("" if c["auto"] else " — posição fixa; use auto ou outra"))
        moved = sum(1 for c in placed if c["position"] != "bottom")
        if moved:
            rep.warn(f"{nome}: {moved} de {len(placed)} bloco(s) fora da base para não cobrir o foco"
                     if position == "auto" else f"{nome}: {moved} bloco(s) com posição fixa fora da base")


def audit_coverage(proj: Path, rep: Report, transcript: Path, threshold: float) -> None:
    sb = load_json(proj / "storyboard.json")
    segs = transcript_segments(load_json(transcript))
    tokens, times = [], []
    for s in segs:
        ws = s.get("words") or [{"text": t, "start": s["start"], "end": s["end"]} for t in words(s["text"])]
        for w in ws:
            for t in words(w["text"]):
                tokens.append(norm_token(t))
                times.append(w["start"])
    for sc in sb["scenes"]:
        for sent in sentences(sc.get("narration", "")):
            target = [norm_token(t) for t in words(sent)]
            n = len(target)
            hits, i = [], 0
            while i + n <= len(tokens):
                ratio = difflib.SequenceMatcher(None, target, tokens[i:i + n]).ratio()
                if ratio >= threshold:
                    hits.append(times[i])
                    i += n
                else:
                    i += 1
            if not hits:
                rep.err(f"{sc['id']}: frase ausente no áudio: “{sent}”")
            elif len(hits) > 1:
                rep.err(f"{sc['id']}: frase repetida {len(hits)}× (retake?) em {[round(h, 1) for h in hits]} s: “{sent}”")


# ---------------------------------------------------------------- composição determinística (spec.json → vídeo)

def cmd_prepare(args) -> int:
    import compose as C
    proj = Path(args.project)
    try:
        msg = C.prepare(proj, project_config(proj), lambda out: cmd_sfx(argparse.Namespace(out=str(out))))
    except C.ComposeError as e:
        die(str(e))
    registrar(proj, "prepare: spec.json → roteiro, step-map, storyboard provisório, brief e esqueleto da composição")
    print(f"{proj}: {msg}")
    return 0


def cmd_compose(args) -> int:
    import compose as C
    proj = Path(args.project)
    try:
        r = C.Composer(proj).build()
    except C.ComposeError as e:
        die(str(e))
    main(["sync-composition", str(proj)])
    print(f"composition/index.html: {r['comandos']} comandos, {r['sobreposicoes']} sobreposições, {r['sons']} sons")
    rep = Report()
    audit_composition(proj, rep)
    return rep.print(f"audit composition — {proj}")


def cmd_capture(args) -> int:
    """T2 por roteiro: screenshots de página inteira + caixas medidas no DOM (sem estimar caixa olhando imagem)."""
    import capture as CAP
    roteiro_f = Path(args.roteiro)
    roteiro = load_json(roteiro_f)
    proj = Path(args.project)
    if not roteiro.get("base"):
        import compose as C
        roteiro["base"] = C.product_info(proj)["url"] or die("roteiro sem 'base' e catálogo sem produto.url")
    try:
        r = CAP.capture(roteiro, proj / args.saida, roteiro.get("navegador") or chrome_path())
    except CAP.CaptureError as e:
        die(str(e))
    registrar(proj, f"captura {roteiro_f.name}: {len(r['fotos'])} tela(s), caixas em {args.saida}/boxes.json")
    print(f"{len(r['fotos'])} captura(s), {r['caixas']} caixas em {proj / args.saida / 'boxes.json'}"
          + (f"; sem caixa: {', '.join(r['faltas'])}" if r["faltas"] else ""))
    return 1 if r["faltas"] else 0


PIPELINE = ("prepare", "tts", "retime", "narration", "compose", "audit", "render", "burn", "final", "idiomas", "estado")


def cmd_produzir(args) -> int:
    """spec.json → vídeo pronto, um comando: cada etapa é script; para no primeiro erro e diz o que falta."""
    proj = Path(args.project)
    de, ate = PIPELINE.index(args.de), PIPELINE.index(args.ate)
    if de > ate:
        die(f"--de {args.de} vem depois de --ate {args.ate} (ordem: {' → '.join(PIPELINE)})")
    etapas = {
        "prepare": [["prepare", str(proj)]],
        "tts": [["tts", str(proj / "script.md")]],
        "retime": [["retime", str(proj)]],
        "narration": [["narration", str(proj)]],
        "compose": [["compose", str(proj)]],
        "audit": [["audit", k, str(proj)] for k in ("storyboard", "captions", "privacy")],
        "render": [["render", str(proj)]],
        "burn": [["burn", str(proj)]],
        "final": [["audit", "final", str(proj)]],
        "idiomas": [["idiomas", str(proj)]],
        # legendas traduzidas entram na checagem de privacidade de novo antes de fechar o estado
        "estado": [["audit", "privacy", str(proj)], ["estado", str(proj)]],
    }
    for nome in PIPELINE[de:ate + 1]:
        for argv in etapas[nome]:
            print(f"\n######## {nome}: tutorial.py {' '.join(argv[:2])}")
            try:
                code = main(argv)
            except SystemExit as e:
                code = e.code if isinstance(e.code, int) else (0 if e.code is None else 2)
            if nome == "idiomas" and code == 3:
                print(f"\nPAROU em idiomas: traduza o campo 'texto' dos idiomas/*/traducao.json e rode: "
                      f"tutorial.py produzir {proj} --de idiomas")
                return 3
            if code:
                print(f"\nPAROU em {nome} (código {code}); corrija e retome com: tutorial.py produzir {proj} --de {nome}")
                return code
    print(f"\n[OK] {proj}: {PIPELINE[de]} → {PIPELINE[ate]} concluído")
    return 0


FASES = (  # (fase, descrição, teste no disco) — a fase atual é a primeira que ainda não passa
    ("T0", "preparar", lambda p, sb, slug: (p / "tutorial.config.json").exists()),
    ("T1", "brief", lambda p, sb, slug: (p / "brief.md").exists() and len((p / "brief.md").read_text(encoding="utf-8").strip()) > 20),
    ("T2", "captura", lambda p, sb, slug: (p / "step-map.json").exists() and any(
        (p / s.get("evidence", "-")).exists() for s in load_json(p / "step-map.json").get("steps", []))),
    ("T3", "marca", lambda p, sb, slug: (p / "composition" / "brand" / "brand.css").exists()),
    ("T4", "roteiro e voz", lambda p, sb, slug: (p / "audio" / "durations.json").exists() and (p / "audio" / "narration.wav").exists()),
    ("T5", "storyboard", lambda p, sb, slug: bool(sb and sb.get("scenes")) and all(s.get("focus_boxes") is not None for s in sb["scenes"])),
    ("T6/T7", "composição", lambda p, sb, slug: (p / "composition" / "index.html").exists() and (p / "composition" / "timeline.js").exists()),
    ("T8", "acabamento", lambda p, sb, slug: (p / "renders" / f"{slug}.mp4").exists() and (p / "renders" / f"{slug}.srt").exists()),
    ("idiomas", "faixas e legendas", lambda p, sb, slug: (p / "idiomas" / "idiomas.json").exists()
        or len(project_config(p).get("idiomas") or IDIOMAS_PADRAO) <= 1),
)


def cmd_estado(args) -> int:
    """Reescreve o topo do ESTADO.md a partir do disco (fase e etapas); decisões e registro ficam como estão."""
    proj = Path(args.project)
    sb = load_json(proj / "storyboard.json") if (proj / "storyboard.json").exists() else None
    slug = ((sb or {}).get("meta") or {}).get("slug") or proj.name
    linhas, atual = [], None
    for fase, desc, ok in FASES:
        try:
            feito = bool(ok(proj, sb, slug))
        except Exception:
            feito = False
        linhas.append(f"| {fase} | {desc} | {'feito' if feito else 'pendente'} |")
        if not feito and atual is None:
            atual = f"{fase} {desc}"
    cfg = project_config(proj)
    aceite = cfg.get("aceite")
    if args.aceite:
        import datetime
        aceite = datetime.date.today().isoformat()
        cf = proj / "tutorial.config.json"
        if not cf.exists():   # criar um config só com "aceite" esconderia o config herdado
            die(f"{cf} não existe (rode tutorial.py init {proj} antes de registrar o aceite)")
        c = load_json(cf)
        c["aceite"] = aceite
        cf.write_text(json.dumps(c, ensure_ascii=False, indent=2), encoding="utf-8")
    atual = atual or ("T9 concluído (aceito em " + aceite + ")" if aceite else "T9 revisão do usuário (P6)")
    bloco = ("<!-- situação gerada por tutorial.py estado a partir do disco; não edite este bloco -->\n"
             f"- Fase atual: {atual}\n- Gates: {cfg.get('gates', 'todos')}\n\n| Fase | Etapa | Situação |\n|---|---|---|\n"
             + "\n".join(linhas) + "\n<!-- fim da situação -->")
    f = proj / "ESTADO.md"
    body = f.read_text(encoding="utf-8") if f.exists() else f"# Estado do tutorial\n\n- Projeto: {slug}\n"
    body = body.replace("\r\n", "\n")
    if "<!-- situação gerada" in body:
        body = re.sub(r"<!-- situação gerada.*?<!-- fim da situação -->", lambda m: bloco, body, flags=re.S)
    else:
        # nada do que a pessoa escreveu se perde: a fase anotada à mão e a tabela de gates viram histórico
        body = re.sub(r"^- Fase atual:(.*)$", r"- Fase anotada à mão (antes do tutorial.py estado):\1", body, flags=re.M)
        body = body.replace("## Gates\n", "## Gates (histórico, anotado à mão)\n", 1)
        partes = body.split("\n## ", 1)
        body = partes[0].rstrip() + "\n\n" + bloco + "\n" + ("\n## " + partes[1] if len(partes) > 1 else "")
    # registro: uma linha por texto (a mesma ação em dias diferentes fica com a última data), só dentro da própria
    # seção; linhas de continuação seguem a linha datada a que pertencem
    m = re.search(r"(## Registro de decisões\n)(.*?)(?=\n## |\Z)", body, flags=re.S)
    if m:
        blocos, ordem, soltas, chave = {}, [], [], None
        for ln in m.group(2).strip("\n").splitlines():
            d = re.match(r"- (\d{4}-\d{2}-\d{2}) · (.*)", ln)
            if d:
                chave = d.group(2)
                cont = []
                if chave in blocos:   # repetido: fica a data mais nova, com a continuação que já existia
                    ordem.remove(chave)
                    cont = blocos[chave][1:]
                blocos[chave] = [ln, *cont]
                ordem.append(chave)
            elif chave is not None and ln.strip():
                blocos[chave].append(ln)
            elif ln.strip():
                soltas.append(ln)
        novo = "\n".join([*soltas, *(l for k in ordem for l in blocos[k])])
        body = body[:m.start(2)] + novo + body[m.end(2):]
    f.write_text(body.rstrip("\n") + "\n", encoding="utf-8", newline="\n")
    print(f"{f}: fase atual {atual}")
    return 0


NONDETERMINISM = re.compile(r"\b(Date\.now|new Date\(|Math\.random|performance\.now|requestAnimationFrame|setTimeout|setInterval)\b")


def scene_range(sb: dict, value: str) -> list[str]:
    """'all', 'c03' ou 'c01-c07' → ids de cena cobertos (na ordem do storyboard)."""
    ids = [s["id"] for s in sb["scenes"]]
    if value == "all":
        return ids
    if "-" in value:
        a, b = value.split("-", 1)
        if a in ids and b in ids:
            return ids[ids.index(a):ids.index(b) + 1]
    return [value] if value in ids else []


def rect_hit(a: list, b: list) -> bool:
    return a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]


def audit_composition(proj: Path, rep: Report) -> None:
    """Checagens que antes dependiam de olhar a composição: cobertura das cenas, áudio com id, arquivos existentes,
    nada de relógio/aleatório, timeline.js em dia com o storyboard e (com compose.json) destaques sem cobrir o clique."""
    comp = proj / "composition"
    html_f = comp / "index.html"
    if not html_f.exists():
        rep.err("composition/index.html ausente (rode tutorial.py compose)")
        return
    sb = load_json(proj / "storyboard.json")
    html = html_f.read_text(encoding="utf-8")
    ids = [s["id"] for s in sb["scenes"]]
    covered = set()
    for tag in re.findall(r"<(?:section|div)\b[^>]*data-scene=\"([^\"]+)\"", html):
        covered.update(scene_range(sb, tag))
    for sid in ids:
        if sid not in covered and f'at("{sid}"' not in html:
            rep.err(f"cena {sid} sem elemento data-scene nem ação na composição")
    for tag in re.findall(r"<audio\b[^>]*>", html):
        attrs = dict(re.findall(r'([\w-]+)="([^"]*)"', tag))
        if not attrs.get("id"):
            rep.err(f"<audio> sem id (o render ignora o som): {tag[:90]}")
        if attrs.get("src") and not (comp / attrs["src"]).exists():
            rep.err(f"áudio não encontrado: {attrs['src']}")
    for src in re.findall(r'<(?:img|link|script)\b[^>]*(?:src|href)="([^"]+)"', html):
        if not re.match(r"^(https?:|data:|#)", src) and not (comp / src.split("?")[0]).exists():
            rep.err(f"arquivo referenciado não existe: {src}")
    for m in re.finditer(r"<script\b[^>]*>(.*?)</script>", html, re.S):
        hit = NONDETERMINISM.search(m.group(1))
        if hit:
            rep.err(f"'{hit.group(1)}' no script da composição: o render quadro a quadro precisa ser determinístico")
    tl_f = comp / "timeline.js"
    if not tl_f.exists():
        rep.err("composition/timeline.js ausente (rode tutorial.py sync-composition)")
    else:
        m = re.search(r"window\.TL\s*=\s*(\{.*\})\s*;?\s*$", tl_f.read_text(encoding="utf-8"), re.S)
        tl = json.loads(m.group(1)) if m else {}
        for s in sb["scenes"]:
            t = (tl.get("scenes") or {}).get(s["id"])
            if not t or abs(t["start"] - s["start"]) > 0.002 or abs(t["end"] - s["end"]) > 0.002:
                rep.err(f"timeline.js desatualizado na cena {s['id']} (rode tutorial.py sync-composition)")
                break
    rep_f = comp / "compose.json"
    if not rep_f.exists():
        rep.warn("sem compose.json: composição escrita à mão; destaques × cliques não foram conferidos")
        return
    cr = load_json(rep_f)
    for sid, c in (cr.get("cenas") or {}).items():
        for o in c.get("sobreposicoes", []):
            x, y, w, h = o["rect"]
            if x < 0 or y < 0 or x + w > 1920 or y + h > 1080:
                rep.err(f"{sid}: {o['tipo']} sai do quadro ({[round(v) for v in o['rect']]})")
            for k in c.get("cliques", []):
                if o["t0"] - 0.05 <= k["t"] <= o["t1"] and rect_hit(o["rect"], k["rect"]):
                    rep.err(f"{sid}: {o['tipo']} cobre o elemento clicado em {k['t']:.2f} s (mude o lado: below/above/left/right)")
        for k in c.get("cliques", []):
            if not k.get("palavra"):
                rep.warn(f"{sid}: clique em {k['t']:.2f} s sem âncora na fala (use \"w:Palavra\" para sincronizar com a voz)")


PRIVACY = {
    # domínio começa com letra e termina em letras: "logo@2x.png" e "gsap@3.14.2" não são e-mail
    "e-mail": re.compile(r"[\w.+-]+@[A-Za-z][\w-]*(?:\.[\w-]+)*\.[A-Za-z]{2,}\b"),
    "CPF": re.compile(r"(?<![\d.])\d{3}\.\d{3}\.\d{3}-\d{2}(?!\d)"),
    "CNPJ": re.compile(r"(?<!\d)\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}(?!\d)"),
    # (11) 98765-4321 · (11) 9 8765-4321 · 11 98765-4321 · 11 3456-7890 (DDD não começa com 0: "08 0800-1800" passa)
    "telefone": re.compile(r"(?:\+?55\s?)?(?:\(\s?[1-9]\d\s?\)\s?(?:9\s?)?\d{4}[-\s]?\d{4}|(?<!\d)[1-9]\d\s(?:9\s?\d{4}|[2-5]\d{3})-\d{4})(?!\d)"),
    "token": re.compile(r"\b(?:sk|pk|ghp|xox[bp])_[A-Za-z0-9]{16,}\b|\beyJ[\w-]{12,}\.[\w-]{8,}"),
}
SO_DIGITOS = re.compile(r"(?<![\w.\-/:])\+?\d{10,14}(?![\w.\-/:])")
EXT_ARQUIVO = re.compile(r"\.(png|jpe?g|svg|webp|gif|js|css|mp4|wav|mp3|json|html?|vtt|srt)$", re.I)
EMAIL_FICTICIO = re.compile(r"@(?:example|exemplo|empresa|teste|test|ficticio|fictício)\.", re.I)


def cpf_valido(d: str) -> bool:
    if len(d) != 11 or d == d[0] * 11:
        return False
    for n in (9, 10):
        s = sum(int(d[i]) * (n + 1 - i) for i in range(n)) % 11
        if int(d[n]) != (0 if s < 2 else 11 - s):
            return False
    return True


def cnpj_valido(d: str) -> bool:
    if len(d) != 14 or d == d[0] * 14:
        return False
    for n, pesos in ((12, [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]), (13, [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])):
        s = sum(int(d[i]) * pesos[i] for i in range(n)) % 11
        if int(d[n]) != (0 if s < 2 else 11 - s):
            return False
    return True


def so_digitos(v: str) -> str | None:
    """Sequência só de dígitos: CPF/CNPJ (dígito verificador confere) ou celular/fixo brasileiro; senão None."""
    d = v.lstrip("+")
    if len(d) == 11 and cpf_valido(d):
        return "CPF"
    if len(d) == 14 and cnpj_valido(d):
        return "CNPJ"
    if len(d) in (12, 13) and d.startswith("55"):
        d = d[2:]
    if len(d) == 11 and d[0] != "0" and d[2] == "9":
        return "telefone"
    if len(d) == 10 and d[0] != "0" and d[2] in "2345":
        return "telefone"
    return None


def ficticio(nome: str, v: str) -> bool:
    """Fictício óbvio: e-mail em domínio de exemplo; número com 5 dígitos iguais seguidos (5511900000001)."""
    if nome == "e-mail":
        return bool(EMAIL_FICTICIO.search(v))
    return bool(re.search(r"(\d)\1{4,}", re.sub(r"\D", "", v)))


def audit_privacy(proj: Path, rep: Report) -> None:
    """Dados pessoais no que vai para o vídeo: roteiro, textos de tela, digitação simulada, composição e legendas.
    Fictícios óbvios passam (domínio example/empresa/teste, dígitos repetidos); outros, em tutorial.config.json >
    privacidade.permitidos. Não lê pixels: capturas continuam exigindo a troca por fictícios no DOM antes da foto."""
    cfg = project_config(proj)
    ok_extra = [re.compile(x, re.I) for x in (cfg.get("privacidade") or {}).get("permitidos", [])]
    fontes: list[tuple[str, str]] = []
    for rel in ("script.md", "spec.json", "storyboard.json", "step-map.json"):
        if (proj / rel).exists():
            fontes.append((rel, (proj / rel).read_text(encoding="utf-8")))
    if (proj / "composition" / "index.html").exists():
        txt = re.sub(r"<script\b.*?</script>|<style\b.*?</style>", " ", (proj / "composition" / "index.html").read_text(encoding="utf-8"), flags=re.S)
        fontes.append(("composition/index.html", re.sub(r"<[^>]+>", " ", txt) + " ".join(
            re.findall(r"textContent:\s*(\"[^\"]*\")", (proj / "composition" / "index.html").read_text(encoding="utf-8")))))
    extras = [*(proj / "composition" / "overrides").glob("*.*")] if (proj / "composition" / "overrides").exists() else []
    if (proj / "idiomas").exists():
        extras += sorted((proj / "idiomas").glob("*/legenda.vtt")) + sorted((proj / "idiomas").glob("*/traducao.json"))
    for f in extras:
        fontes.append((f.relative_to(proj).as_posix(), f.read_text(encoding="utf-8")))
    vistos = set()

    def achar(nome: str, v: str, rel: str) -> None:
        if ficticio(nome, v) or any(o.search(v) for o in ok_extra) or (nome, v) in vistos:
            return
        vistos.add((nome, v))
        rep.err(f"{nome} em {rel}: '{v}' — troque por fictício ou declare em privacidade.permitidos")

    for rel, text in fontes:
        for nome, rx in PRIVACY.items():
            for m in rx.finditer(text):
                if nome == "e-mail" and EXT_ARQUIVO.search(m.group(0)):
                    continue   # nome de arquivo com @ (logo@2x.png), não e-mail
                achar(nome, m.group(0), rel)
        for m in SO_DIGITOS.finditer(text):
            tipo = so_digitos(m.group(0))
            if tipo:
                achar(tipo, m.group(0), rel)


def cmd_audit(args) -> int:
    proj = Path(args.project)
    rep = Report()
    if args.kind == "composition":
        audit_composition(proj, rep)
    elif args.kind == "privacy":
        audit_privacy(proj, rep)
    elif args.kind == "storyboard":
        audit_storyboard(proj, rep)
    elif args.kind == "final":
        audit_final(proj, rep, Path(args.render) if args.render else None)
    elif args.kind == "brand":
        audit_brand(proj, rep)
    elif args.kind == "captions":
        audit_captions(proj, rep)
    elif args.kind == "coverage":
        if not args.transcript:
            die("--transcript é obrigatório para 'coverage'")
        audit_coverage(proj, rep, proj / args.transcript if not Path(args.transcript).is_absolute() else Path(args.transcript), args.threshold)
    return rep.print(f"audit {args.kind} — {proj}")


def cmd_set_key(args) -> int:
    """Configura e valida a chave de API (interativo, flag ou salvamento em .env e/ou variáveis do sistema)."""
    key = args.key
    cur_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        if cur_key:
            masked = cur_key[:6] + "..." + cur_key[-4:] if len(cur_key) > 10 else "***"
            print(f"Chave atual configurada: {masked}")
        if sys.stdin.isatty():
            try:
                prompt_text = "Cole a chave GEMINI_API_KEY do Google AI Studio: " if not cur_key else "Cole a nova chave GEMINI_API_KEY (ou Enter para manter): "
                key = input(prompt_text).strip()
            except (KeyboardInterrupt, EOFError):
                print()
                return 0
        elif not cur_key:
            die("Informe a chave via: tutorial set-key --key SUA_CHAVE")

    if not key:
        if cur_key:
            key = cur_key
            print("Mantendo a chave atual.")
        else:
            print("Nenhuma chave informada.")
            return 1

    os.environ["GEMINI_API_KEY"] = key

    # Validação com Google AI Studio
    if not args.no_check:
        print("Validando chave com Google AI Studio...", end=" ", flush=True)
        try:
            from google import genai
            client = genai.Client(api_key=key)
            _ = list(client.models.list(config={"page_size": 2}))
            print("OK (conexão bem-sucedida!)")
        except Exception as e:
            print(f"Aviso na verificação: {e}")

    saved = []
    # 1. Salvar no .env do workspace raiz
    workspace_root = HOME.parent if HOME.name == "aidd-materialize-tutorial-stitch" else HOME
    env_path = workspace_root / ".env"
    try:
        content = env_path.read_text(encoding="utf-8-sig") if env_path.exists() else ""
        if "GEMINI_API_KEY=" in content:
            new_content = re.sub(r"GEMINI_API_KEY=.*", f"GEMINI_API_KEY={key}", content)
        else:
            new_content = content + f"\nGEMINI_API_KEY={key}\n"
        env_path.write_text(new_content.strip() + "\n", encoding="utf-8")
        saved.append(f"arquivo .env ({env_path.name})")
    except Exception as e:
        print(f"Aviso ao salvar .env: {e}")

    # 2. Salvar como variável de ambiente permanente do Windows
    save_system = args.system
    if not save_system and sys.stdin.isatty() and platform.system() == "Windows":
        try:
            resp = input("Deseja salvar permanentemente no Windows para seu Usuário? [S/n]: ").strip().lower()
            if resp in ("", "s", "sim", "y", "yes"):
                save_system = True
        except Exception:
            pass

    if save_system and platform.system() == "Windows":
        try:
            r = subprocess.run(["setx", "GEMINI_API_KEY", key], capture_output=True, text=True)
            if r.returncode == 0:
                saved.append("Variável de Ambiente do Windows (Permanente)")
            else:
                saved.append(f"Falha ao registrar Windows: {r.stderr.strip()}")
        except Exception as e:
            saved.append(f"Erro ao registrar Windows: {e}")

    print(f"Sucesso! Chave registrada em: {', '.join(saved)}.")
    return 0


# ---------------------------------------------------------------- CLI

def main(argv=None) -> int:
    raw_argv = sys.argv[1:] if argv is None else list(argv)
    argv = extract_global_flags(raw_argv)

    p = argparse.ArgumentParser(prog="tutorial.py", description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("doctor", help="verifica dependências (somente leitura)").set_defaults(fn=cmd_doctor)

    s = sub.add_parser("set-key", help="configura a chave GEMINI_API_KEY (interativo, flag, .env e/ou Windows)")
    s.add_argument("--key", help="chave GEMINI_API_KEY do Google AI Studio (se omitido, pergunta no terminal)")
    s.add_argument("--system", action="store_true", help="grava também nas Variáveis de Ambiente do Usuário do Windows")
    s.add_argument("--no-check", action="store_true", help="pula o teste de conexão com o Google AI Studio")
    s.set_defaults(fn=cmd_set_key)

    s = sub.add_parser("init", help="cria a estrutura de um projeto de tutorial (aceita as flags da skill)")
    s.add_argument("dir")
    s.add_argument("--force", action="store_true")
    add_flag_args(s)
    s.set_defaults(fn=cmd_init)

    s = sub.add_parser("config", help="mostra ou altera as flags gravadas em tutorial.config.json")
    s.add_argument("dir")
    add_flag_args(s)
    s.set_defaults(fn=cmd_config)

    s = sub.add_parser("timing", help="estima a duração da narração por cena")
    s.add_argument("script")
    s.add_argument("--wps", type=float, default=2.5, help="palavras por segundo (padrão 2,5)")
    s.add_argument("--gap", type=float, default=0.4, help="respiro após a fala (s)")
    s.add_argument("--silent", type=float, default=2.0, help="duração de cena sem fala (s)")
    s.add_argument("--target", type=float, help="duração alvo do brief (s)")
    s.set_defaults(fn=cmd_timing)

    s = sub.add_parser("tts", help="gera a voz de cada cena, mede durações e grava os tempos por palavra")
    s.add_argument("script")
    s.add_argument("--engine", choices=["auto", *TTS_ENGINES, "none"],
                   help="padrão: tutorial.config.json > voice.engine, senão auto (edge → gemini → kokoro → system)")
    s.add_argument("--voice", help="edge: pt-BR-FranciscaNeural | gemini: Kore, Charon, Puck… | fish: reference_id | "
                                   "kokoro: pf_dora | system: 'Microsoft Maria Desktop'")
    s.add_argument("--lang")
    s.add_argument("--speed", type=float)
    s.add_argument("--model", help="modelo do Gemini TTS (padrão: TC_GEMINI_TTS_MODEL ou gemini-2.5-flash-preview-tts)")
    s.add_argument("--out")
    s.set_defaults(fn=cmd_tts)

    s = sub.add_parser("responsive", help="testa se o app é responsivo nos formatos pedidos (somente leitura)")
    s.add_argument("url")
    s.add_argument("--out", required=True)
    s.add_argument("--formatos", help="16:9,9:16,1:1,4:5 (padrão 9:16)")
    s.add_argument("--atalho", help="rótulo do botão de entrada de teste (opcional)")
    s.add_argument("--papel-atalho", dest="papel_atalho", default="button", choices=["button", "link"])
    s.add_argument("--caminhos", help="rotas a medir depois de entrar (vírgulas)")
    s.add_argument("--projeto", help="grava o resultado no tutorial.config.json e no ESTADO.md deste projeto")
    s.add_argument("--chrome")
    s.set_defaults(fn=cmd_responsive)

    s = sub.add_parser("voices", help="catálogo de vozes por motor e idioma, com amostras em áudio (VOZES.md)")
    s.add_argument("out", help="pasta onde gravar VOZES.md e amostras/")
    s.add_argument("--motores", help="edge,gemini,kokoro,system (padrão: edge,gemini)")
    s.add_argument("--idioma", default="pt-BR")
    s.add_argument("--amostras", action="store_true", help="gera um áudio curto por voz para ouvir")
    s.add_argument("--texto", help="frase das amostras")
    s.add_argument("--limite", type=int, help="no máximo N vozes por motor")
    s.add_argument("--so-nativas", dest="so_nativas", action="store_true", help="omite vozes multilíngues de outro idioma")
    s.set_defaults(fn=cmd_voices)

    s = sub.add_parser("retime", help="recalcula start/end das cenas a partir de audio/durations.json")
    s.add_argument("project")
    s.add_argument("--gap", type=float, default=0.4)
    s.set_defaults(fn=cmd_retime)

    s = sub.add_parser("narration", help="monta audio/narration.wav na linha do tempo do storyboard")
    s.add_argument("project")
    s.set_defaults(fn=cmd_narration)

    s = sub.add_parser("frames", help="extrai frames de um vídeo (por cena, intervalo ou tempos)")
    s.add_argument("video")
    s.add_argument("--out", required=True)
    s.add_argument("--scene", type=float, default=0.25, help="limiar de mudança de cena (0-1)")
    s.add_argument("--every", type=float, help="um frame a cada N segundos")
    s.add_argument("--at", help="tempos exatos separados por vírgula")
    s.add_argument("--sheet", action="store_true", help="gera contact-sheet.jpg")
    s.add_argument("--largura", type=int, default=800, help="largura dos quadros (padrão 800; 0 = original)")
    s.set_defaults(fn=cmd_frames)

    s = sub.add_parser("record", help="grava a tela/janela enquanto o usuário executa o fluxo")
    s.add_argument("--seconds", type=float, required=True)
    s.add_argument("--out", required=True)
    s.add_argument("--window", help="título da janela (Windows)")
    s.add_argument("--device", help="dispositivo avfoundation (macOS), p.ex. '1:none'")
    s.add_argument("--fps", type=int, default=30)
    s.set_defaults(fn=cmd_record)

    s = sub.add_parser("reference", help="baixa/abre um vídeo, transcreve e extrai frames")
    s.add_argument("source", help="URL do YouTube ou caminho de arquivo")
    s.add_argument("--out", required=True)
    s.add_argument("--lang", help="idioma da fala (p.ex. pt, en); omita para detectar")
    s.add_argument("--model", default="small")
    s.add_argument("--every", type=float, help="frames a cada N s em vez de por cena")
    s.add_argument("--scene", type=float, default=0.25)
    s.set_defaults(fn=cmd_reference)

    s = sub.add_parser("captions", help="transcreve uma mídia e gera .srt + transcript.json")
    s.add_argument("media")
    s.add_argument("--out")
    s.add_argument("--lang", default="pt")
    s.add_argument("--model", default="small")
    s.set_defaults(fn=cmd_captions)

    s = sub.add_parser("burn", help="queima legendas estilizadas no render e gera .srt/.ass")
    s.add_argument("project")
    s.add_argument("--style", choices=[*CAPTION_STYLES, "none"],
                   help="padrão: tutorial.config.json > captions.style, senão highlight (16:9) / bold-pop (9:16)")
    s.add_argument("--input", help="render sem legenda (padrão renders/<slug>.raw.mp4)")
    s.add_argument("--out", help="saída (padrão renders/<slug>.mp4)")
    s.add_argument("--font")
    s.add_argument("--accent", help="cor da palavra ativa, hex (padrão #FFD43B)")
    s.add_argument("--case", choices=["normal", "upper", "lower"])
    s.add_argument("--position", choices=["auto", *CAPTION_POSITIONS],
                   help="padrão: captions.position ou auto (cada bloco longe do foco do passo)")
    s.add_argument("--size", choices=list(CAPTION_SIZES), help="p, m (padrão) ou g")
    s.add_argument("--lang")
    s.set_defaults(fn=cmd_burn)

    s = sub.add_parser("render", help="renderiza composition/ em renders/<slug>.raw.mp4 com novas tentativas")
    s.add_argument("project")
    s.add_argument("--quality", choices=["rascunho", "final"])
    s.add_argument("--composicao", help="pasta de uma composição nativa em outro formato (ex.: composition-9x16)")
    s.add_argument("--formato", choices=list(FORMATS), help="formato da composição nativa (com --composicao)")
    s.set_defaults(fn=cmd_render)

    s = sub.add_parser("export", help="gera as saídas (formatos × resoluções × canais) a partir do render-mestre")
    s.add_argument("project")
    s.add_argument("--canal", help="presets de canal (vírgulas): " + ", ".join(CHANNELS))
    s.add_argument("--formatos", help="16:9,9:16,1:1,4:5")
    s.add_argument("--resolucoes", help="480p,720p,1080p")
    s.add_argument("--legenda", choices=[*CAPTION_STYLES, "nenhuma"], help="sobrescreve o estilo de legenda destas saídas")
    s.add_argument("--modo", choices=["auto", "escalar", "reenquadrar", "nativo"], default="auto")
    s.add_argument("--recorte", type=float, help="proporção da zona central recortada no reenquadramento (padrão 1.185)")
    s.set_defaults(fn=cmd_export)

    s = sub.add_parser("sfx", help="gera efeitos sonoros discretos (click, pop, whoosh, tick)")
    s.add_argument("out")
    s.set_defaults(fn=cmd_sfx)

    s = sub.add_parser("sync-composition", help="grava composition/timeline.js e ajusta data-start/duration por data-scene")
    s.add_argument("project")
    s.add_argument("--html", default="index.html")
    s.add_argument("--composicao", help="pasta da composição (padrão composition; ex.: composition-9x16)")
    s.set_defaults(fn=cmd_sync_composition)

    s = sub.add_parser("catalog", help="catálogo de tutoriais de um produto: render | next | add | remove | set")
    s.add_argument("op", choices=["render", "next", "add", "remove", "set"])
    s.add_argument("dir", help="pasta do produto (contém catalogo.json)")
    s.add_argument("--slug")
    s.add_argument("--titulo")
    s.add_argument("--perfil")
    s.add_argument("--jornada")
    s.add_argument("--objetivo")
    s.add_argument("--tipo", choices=["observacao", "acao"])
    s.add_argument("--duracao", type=int)
    s.add_argument("--prioridade", type=int, choices=[1, 2, 3])
    s.add_argument("--status", choices=list(CATALOG_STATUS))
    s.set_defaults(fn=cmd_catalog)

    s = sub.add_parser("capture", help="T2 por roteiro JSON: telas de página inteira + caixas medidas no DOM (boxes.json)")
    s.add_argument("project")
    s.add_argument("--roteiro", required=True, help="roteiro.json (references/02-captura-por-alvo.md §W1)")
    s.add_argument("--saida", default="evidence", help="pasta de saída, relativa ao projeto (padrão evidence)")
    s.set_defaults(fn=cmd_capture)

    s = sub.add_parser("prepare", help="spec.json → roteiro, step-map, storyboard provisório, brief e esqueleto da composição")
    s.add_argument("project")
    s.set_defaults(fn=cmd_prepare)

    s = sub.add_parser("compose", help="spec.json + voz medida → composition/index.html (sem HTML à mão) + sync + audit")
    s.add_argument("project")
    s.set_defaults(fn=cmd_compose)

    s = sub.add_parser("produzir", help="spec.json → vídeo pronto: prepare, voz, compose, audits, render, legenda, idiomas")
    s.add_argument("project")
    s.add_argument("--de", choices=PIPELINE, default="prepare")
    s.add_argument("--ate", choices=PIPELINE, default="estado")
    s.set_defaults(fn=cmd_produzir)

    s = sub.add_parser("estado", help="reescreve a situação do ESTADO.md a partir do disco (fase e etapas)")
    s.add_argument("project")
    s.add_argument("--aceite", action="store_true", help="registra o aceite do usuário (P6)")
    s.set_defaults(fn=cmd_estado)

    s = sub.add_parser("idiomas", help="faixa de áudio e legenda por idioma sobre a mesma imagem (só a tradução é do agente)")
    s.add_argument("project")
    s.add_argument("--idiomas", help="lista (vírgulas); padrão: tutorial.config.json > idiomas, ou pt-BR,en-US,es")
    s.add_argument("--preparar", action="store_true", help="só cria/atualiza os traducao.json e diz o que falta")
    s.set_defaults(fn=cmd_idiomas)

    s = sub.add_parser("empresa", help="vitrine de uma empresa com vários aplicativos: init | add-app | remove-app | list")
    s.add_argument("op", choices=["init", "add-app", "remove-app", "list"])
    s.add_argument("dir", help="pasta da empresa (contém empresa.json)")
    s.add_argument("--nome")
    s.add_argument("--slug")
    s.add_argument("--pasta", help="add-app: pasta do aplicativo (com catalogo.json)")
    s.add_argument("--descricao")
    s.set_defaults(fn=cmd_empresa)

    s = sub.add_parser("vitrine", help="monta <empresa>/site/ (página, vídeos, capas, prévias) a partir dos catálogos")
    s.add_argument("dir", help="pasta da empresa (contém empresa.json)")
    s.add_argument("--publicar", action="store_true", help="envia à VPS em seguida (só o que mudou)")
    s.set_defaults(fn=cmd_vitrine)

    s = sub.add_parser("publicar", help="refaz a vitrine e envia à VPS só o que mudou; --auto on|off liga a publicação automática")
    s.add_argument("dir", help="pasta da empresa (contém empresa.json)")
    s.add_argument("--auto", choices=["on", "off"], help="grava no empresa.json se cada 'catalog render' publica sozinho")
    s.add_argument("--dry-run", action="store_true", help="mostra o que seria enviado/removido, sem enviar")
    s.add_argument("--limpar", action="store_true", help="remove do servidor arquivos que o manifest não conhece")
    s.add_argument("--forcar", action="store_true", help="reenvia tudo")
    s.add_argument("--sem-gerar", action="store_true", help="envia o site como está, sem refazer")
    s.set_defaults(fn=cmd_publicar)

    s = sub.add_parser("design-tokens", help="extrai o design system do produto (de um hyperframes capture) para "
                                             "design-tokens.json + brand/brand.css")
    s.add_argument("capture", help="pasta gerada por: npx hyperframes capture <url> -o <pasta>")
    s.add_argument("--out", required=True, help="pasta do projeto ou do catálogo (compartilhado/)")
    s.set_defaults(fn=cmd_design_tokens)

    s = sub.add_parser("extract-rea", help="salva as imagens PNG inline de um resultado do REA")
    s.add_argument("result")
    s.add_argument("out")
    s.set_defaults(fn=cmd_extract_rea)

    s = sub.add_parser("audit", help="audita storyboard, render final ou cobertura da narração")
    s.add_argument("kind", choices=["storyboard", "final", "coverage", "brand", "captions", "composition", "privacy"])
    s.add_argument("project")
    s.add_argument("--render", help="caminho do MP4 (padrão: o mais recente em renders/)")
    s.add_argument("--transcript", help="transcrição JSON do áudio final (coverage)")
    s.add_argument("--threshold", type=float, default=0.8)
    s.set_defaults(fn=cmd_audit)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
