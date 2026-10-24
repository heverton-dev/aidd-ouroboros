"""Vitrine da empresa (vários aplicativos) e publicação incremental.

Rode: python tests/smoke/test_vitrine.py  (exige ffmpeg; a publicação usa um ssh falso, nada sai da máquina)
"""
from __future__ import annotations

import io
import json
import shutil
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

SMOKE = Path(__file__).resolve().parent
sys.path.insert(0, str(SMOKE.parent.parent / "aidd-skills" / "aidd-materialize-tutorial-stitch" / "scripts"))
import tutorial as T  # noqa: E402


def fake_render(renders: Path, slug: str, secs: int = 3) -> None:
    renders.mkdir(parents=True, exist_ok=True)
    # tutorial só em português: não espera faixas de outros idiomas para entrar na vitrine
    (renders.parent / "tutorial.config.json").write_text(json.dumps({"idiomas": ["pt-BR"]}), encoding="utf-8")
    for name in (f"{slug}.mp4", f"{slug}.raw.mp4"):
        r = T.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"testsrc2=size=320x180:rate=24:duration={secs}",
                   "-f", "lavfi", "-i", f"sine=duration={secs}", "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                   str(renders / name)], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
    (renders / f"{slug}.srt").write_text("1\n00:00:00,000 --> 00:00:01,000\nOlá\n", encoding="utf-8")


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        emp = self.tmp / "empresa"
        T.cmd_empresa(SimpleNamespace(op="init", dir=str(emp), nome="Acme", slug=None))
        for n in T.MARCA_ARQUIVOS:
            (emp / "marca" / n).write_bytes(b"x")
        self.emp = emp
        for slug, nome, tuts in (("app-a", "App A", [("um", "gerado"), ("dois", "sugerido"), ("tres", "bloqueado")]),
                                 ("app-b", "App B", [("quatro", "gerado")])):
            root = self.tmp / slug
            root.mkdir()
            cat = {"produto": {"nome": nome, "url": "x"}, "jornadas": ["J1"], "tutoriais": []}
            for s, st in tuts:
                cat["tutoriais"].append({"slug": s, "titulo": s.title(), "jornada": "J1", "status": st, "pasta": f"t/{s}"})
                if st == "gerado":
                    fake_render(root / "t" / s / "renders", s)
            T.catalog_save(root, cat)
            T.cmd_empresa(SimpleNamespace(op="add-app", dir=str(emp), pasta=str(root), nome=None, slug=None, descricao=None))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def data(self) -> dict:
        html = (self.emp / "site" / "index.html").read_text(encoding="utf-8")
        start = html.index('type="application/json">') + len('type="application/json">')
        return json.loads(html[start:html.index("</script>", start)])


@unittest.skipUnless(T.which("ffmpeg"), "ffmpeg ausente")
class Vitrine(Base):

    def test_dois_aplicativos_numa_pagina_sem_bloqueados(self):
        m = T.vitrine_build(self.emp)
        d = self.data()
        self.assertEqual([a["slug"] for a in d["aplicativos"]], ["app-a", "app-b"])
        self.assertEqual(sorted(t["id"] for t in d["tutoriais"]), ["app-a/dois", "app-a/um", "app-b/quatro"])
        um = next(t for t in d["tutoriais"] if t["id"] == "app-a/um")
        self.assertTrue(um["video"].startswith("apps/app-a/videos/01-um.mp4?v="))
        self.assertIn("apps/app-b/previas/01-quatro.mp4", m["arquivos"])
        self.assertEqual(d["proximo_s"], 5)
        self.assertNotIn("{{", (self.emp / "site" / "index.html").read_text(encoding="utf-8"))
        # o catálogo do aplicativo aponta de volta para a empresa (é o que liga a publicação automática)
        self.assertEqual(T.catalog_load(self.tmp / "app-a")["empresa"], "../empresa")

    def test_rodar_de_novo_nao_muda_nada(self):
        v1 = T.vitrine_build(self.emp)["versao"]
        idx = self.emp / "site" / "index.html"
        before = idx.stat().st_mtime_ns
        self.assertEqual(T.vitrine_build(self.emp)["versao"], v1)
        self.assertEqual(idx.stat().st_mtime_ns, before)

    def test_com_tres_idiomas_so_entra_quando_as_faixas_ficam_prontas(self):
        cfg = self.tmp / "app-a" / "t" / "um" / "tutorial.config.json"
        cfg.write_text(json.dumps({"idiomas": ["pt-BR", "en-US", "es"]}), encoding="utf-8")
        T.vitrine_build(self.emp)
        um = next(t for t in self.data()["tutoriais"] if t["id"] == "app-a/um")
        self.assertIsNone(um["video"])                     # vídeo pronto mas sem idiomas: "em breve"

    def test_tutorial_refeito_muda_a_versao_e_aplicativo_removido_sai_do_site(self):
        v1 = T.vitrine_build(self.emp)["versao"]
        fake_render(self.tmp / "app-a" / "t" / "um" / "renders", "um", secs=4)
        self.assertNotEqual(T.vitrine_build(self.emp)["versao"], v1)
        T.cmd_empresa(SimpleNamespace(op="remove-app", dir=str(self.emp), slug="app-b"))
        m = T.vitrine_build(self.emp)
        self.assertFalse(any(p.startswith("apps/app-b/") for p in m["arquivos"]))
        self.assertFalse((self.emp / "site" / "apps" / "app-b").exists())


@unittest.skipUnless(T.which("ffmpeg"), "ffmpeg ausente")
class Idiomas(Base):
    """Tutorial com idiomas/idiomas.json: HLS com uma imagem e uma faixa de áudio por idioma, sem mp4 duplicado."""

    def test_hls_com_faixas_por_idioma_e_sem_mp4(self):
        proj = self.tmp / "app-a" / "t" / "um"
        d = proj / "idiomas"
        man = []
        for lang, nome in (("pt-BR", "Português"), ("en-US", "English")):
            (d / lang).mkdir(parents=True)
            r = T.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "sine=duration=3", "-c:a", "aac",
                       str(d / lang / "faixa.m4a")], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            (d / lang / "legenda.vtt").write_text("WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nOi\n", encoding="utf-8")
            man.append({"idioma": lang, "nome": nome, "faixa": f"{lang}/faixa.m4a", "legenda": f"{lang}/legenda.vtt"})
        (d / "idiomas.json").write_text(json.dumps({"origem": "pt-BR", "video": "renders/um.raw.mp4", "idiomas": man}),
                                        encoding="utf-8")
        m = T.vitrine_build(self.emp)
        um = next(t for t in self.data()["tutoriais"] if t["id"] == "app-a/um")
        self.assertTrue(um["stream"].endswith("/master.m3u8"))
        self.assertEqual(um["video"], um["stream"])
        self.assertEqual([x["idioma"] for x in um["idiomas"]], ["pt-BR", "en-US"])
        self.assertNotIn("apps/app-a/videos/01-um.mp4", m["arquivos"])
        self.assertIn("assets/js/hls.min.js", m["arquivos"])
        master = (self.emp / "site" / um["stream"]).read_text(encoding="utf-8")
        self.assertEqual(master.count("TYPE=AUDIO"), 2)
        self.assertIn('LANGUAGE="en-US"', master)
        # o app sem idiomas continua com o mp4 de sempre
        self.assertIn("apps/app-b/videos/01-quatro.mp4", m["arquivos"])


@unittest.skipUnless(T.which("ffmpeg"), "ffmpeg ausente")
class Publicar(Base):
    """Servidor falso em memória: ssh_run responde ao cat/find/rm; ssh_pipe recebe o tar."""

    def setUp(self):
        super().setUp()
        e = T.empresa_load(self.emp)
        e["publicacao"] = {"ssh": "fake", "pasta_vps": "/srv/site", "dominio": "", "automatica": False}
        T.empresa_save(self.emp, e)
        self.remote: dict[str, bytes] = {}
        self.orig = (T.ssh_run, T.ssh_pipe)
        test = self

        def ssh_run(host, cmd, **kw):
            out = ""
            if cmd.startswith("cat "):
                out = test.remote.get("manifest.json", b"").decode()
            elif "find . -type f" in cmd and "rm -f" not in cmd:
                out = "\n".join("./" + p for p in test.remote)
            elif "rm -f" in cmd:   # a lista chega pela entrada, separada por \0 (xargs -0)
                for p in (kw.get("input") or "").split("\0"):
                    test.remote.pop(p, None)
            return SimpleNamespace(returncode=0, stdout=out, stderr="")

        class Pipe:
            def __init__(self):
                self.stdin = io.BytesIO()
                self.stdin.close = lambda: None
                self.returncode = 0

            def wait(self):
                self.stdin.seek(0)
                with tarfile.open(fileobj=self.stdin, mode="r|") as tar:
                    for m in tar:
                        test.remote[m.name] = tar.extractfile(m).read()
                return 0

        T.ssh_run, T.ssh_pipe = ssh_run, lambda host, cmd: Pipe()

    def tearDown(self):
        T.ssh_run, T.ssh_pipe = self.orig
        super().tearDown()

    def test_envia_tudo_na_primeira_e_nada_na_segunda(self):
        m = T.vitrine_build(self.emp)
        T.vitrine_publish(self.emp)
        self.assertEqual(set(self.remote), set(m["arquivos"]) | {"manifest.json"})
        sent = dict(self.remote)
        self.remote.clear()
        self.remote["manifest.json"] = sent["manifest.json"]
        T.vitrine_publish(self.emp)
        self.assertEqual(set(self.remote), {"manifest.json"})   # nada reenviado

    def test_so_o_que_mudou_e_o_que_saiu_e_removido(self):
        T.vitrine_build(self.emp)
        T.vitrine_publish(self.emp)
        fake_render(self.tmp / "app-a" / "t" / "um" / "renders", "um", secs=4)
        T.cmd_empresa(SimpleNamespace(op="remove-app", dir=str(self.emp), slug="app-b"))
        T.vitrine_build(self.emp)
        quatro = self.remote["apps/app-b/videos/01-quatro.mp4"]
        self.assertTrue(quatro)
        self.remote["apps/app-a/capas/01-um.jpg"] = b"velha"
        T.vitrine_publish(self.emp)
        self.assertNotIn("apps/app-b/videos/01-quatro.mp4", self.remote)
        self.assertNotEqual(self.remote["apps/app-a/capas/01-um.jpg"], b"velha")


if __name__ == "__main__":
    unittest.main(verbosity=2)
