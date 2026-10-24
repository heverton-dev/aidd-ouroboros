# Rode: python tests/tools/regressao_compose.py .   (compara o compose global com as composições do Cadastros)
"""Regressão do compose: specs.py (consultor/equipe) → spec.json numa cópia de cada tutorial; compose; compara com o original.
Igual sem sync (o original não passou por sync-composition) ou igual com sync."""
import importlib.util, json, shutil, sys, tempfile, difflib
from pathlib import Path

REPO = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(REPO / "aidd-tutorial-creator" / "scripts"))
import compose as C  # noqa: E402
import tutorial as TT  # noqa: E402

ROOT = REPO / "cadastros-conexao"
CAT = json.loads((ROOT / "catalogo.json").read_text(encoding="utf-8"))
PASTA = {t["slug"]: t.get("pasta") for t in CAT["tutoriais"]}


def load_specs(d):
    sys.path.insert(0, str(d))
    spec = importlib.util.spec_from_file_location(f"specs_{d.name}", d / "specs.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    sys.path.pop(0)
    return m


def compare(src, dst):
    bad = []
    for rel in ("composition/index.html", "storyboard.json", "step-map.json"):
        a = (src / rel).read_text(encoding="utf-8").splitlines()
        b = (dst / rel).read_text(encoding="utf-8").splitlines()
        d = [l for l in difflib.unified_diff(a, b, lineterm="", n=0) if l[:1] in "+-" and l[:3] not in ("+++", "---")]
        d = [l for l in d if "gerado por" not in l]
        if d:
            bad.append((rel, d))
    return bad


tmp = Path(tempfile.mkdtemp())
falhas = 0
for grupo in ("consultor", "equipe"):
    m = load_specs(ROOT / "04-geradores" / grupo)
    for slug, T in m.TUTORIAIS.items():
        if not PASTA.get(slug) or not (ROOT / PASTA[slug] / "composition" / "index.html").exists():
            continue
        src = ROOT / PASTA[slug]
        dst = tmp / src.name
        shutil.rmtree(dst, ignore_errors=True)
        (dst / "composition").mkdir(parents=True)
        for f in ("storyboard.json", "step-map.json"):
            shutil.copy2(src / f, dst / f)
        shutil.copytree(src / "audio", dst / "audio", ignore=shutil.ignore_patterns("*.wav"))
        shutil.copytree(src / "evidence", dst / "evidence")
        shutil.copytree(src / "composition" / "brand", dst / "composition" / "brand")
        spec = json.loads(json.dumps(T))
        spec["url"] = "https://cadastros.vpsconexao.org"
        spec["marca"] = "Conexão Digital Implant"
        spec.setdefault("rota", "/consultor")
        spec["caixas"] = {k: list(v) for k, v in m.H.items()}
        (dst / "spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
        C.Composer(dst).build()
        bad, modo = compare(src, dst), "sem sync"
        if bad:
            TT.main(["sync-composition", str(dst)])
            bad, modo = compare(src, dst), "com sync"
        for rel, d in bad:
            print(f"  {slug} {rel}: {len(d)} linhas diferentes")
            print("    " + "\n    ".join(d[:6]))
        print(("IGUAL  " if not bad else "DIFERE ") + f"{grupo}/{slug} ({modo})")
        falhas += bool(bad)
        TT.main(["sync-composition", str(dst)]) if modo == "sem sync" else None
        rep = TT.Report(); TT.audit_composition(dst, rep)
        for e in rep.errors + ["AVISO " + w for w in rep.warnings]: print("   audit:", e)
print("falhas:", falhas)
sys.exit(1 if falhas else 0)
