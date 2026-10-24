"""Posição automática da legenda por bloco e audit de colisão legenda × foco do passo.

Rode: python tests/smoke/test_captions.py  (só biblioteca padrão; o teste de burn exige ffmpeg)
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

SMOKE = Path(__file__).resolve().parent
sys.path.insert(0, str(SMOKE.parent.parent / "aidd-skills" / "aidd-materialize-tutorial-stitch" / "scripts"))
import tutorial as T  # noqa: E402


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8-sig"))


def save(p: Path, data: dict) -> None:
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def audit(proj: Path) -> T.Report:
    rep = T.Report()
    T.audit_captions(proj, rep)
    return rep


class Base(unittest.TestCase):
    """Cópia descartável do projeto smoke (só os arquivos que a legenda lê)."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tc-captions-"))
        self.proj = self.tmp / "smoke"
        self.proj.mkdir()
        for f in ("storyboard.json", "step-map.json", "tutorial.config.json"):
            shutil.copyfile(SMOKE / f, self.proj / f)
        shutil.copytree(SMOKE / "audio", self.proj / "audio", ignore=shutil.ignore_patterns("*.wav"))
        (self.proj / "renders").mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def edit(self, name: str, fn) -> None:
        data = load(self.proj / name)
        fn(data)
        save(self.proj / name, data)

    def target_at_bottom(self) -> None:
        """Seletor 'Período' (s02, cena c03) levado para a faixa de baixo da tela, onde a legenda mora."""
        def fn(sm):
            sm["steps"][1]["target_box"] = [552, 1000, 226, 60]
        self.edit("step-map.json", fn)
        self.edit("storyboard.json", lambda sb: sb["meta"].update(screen_box=[0, 0, 1920, 1080]))

    def placements(self) -> list[dict]:
        sb = load(self.proj / "storyboard.json")
        cues = T.group_cues(T.project_words(self.proj, sb), 5, 3.4)
        cap = T.project_config(self.proj)["captions"]
        return T.place_captions(cues, "highlight", 1920, 1080, cap.get("position", "auto"), "m", "normal",
                                T.project_focus_boxes(self.proj, sb), T.scene_caption_positions(sb))


class Geometry(unittest.TestCase):
    def test_zoom_lido_do_campo_ou_da_camera(self):
        self.assertEqual(T.scene_zoom({"camera": "zoom 1,6× no target_box s01"}), 1.6)
        self.assertEqual(T.scene_zoom({"camera": "zoom 2x no botão"}), 2.0)
        self.assertEqual(T.scene_zoom({"camera": "drift 3 %"}), 1.0)
        self.assertEqual(T.scene_zoom({"camera": "zoom 1,6×", "zoom": 2.2}), 2.2)

    def test_target_box_vai_da_captura_ao_quadro_com_zoom_no_centro(self):
        sb = load(SMOKE / "storyboard.json")
        boxes = T.scene_focus_boxes(sb, load(SMOKE / "step-map.json"))
        # s01 [18,174,330,63] a 2/3 em (320,150) → centro (442, 287); zoom 1,6 → 352 × 67,2
        (b,) = boxes["c02"]
        self.assertEqual(b["src"], "target_box s01")
        self.assertAlmostEqual(b["box"][0] + b["box"][2] / 2, 442, delta=0.2)
        self.assertAlmostEqual(b["box"][1] + b["box"][3] / 2, 287, delta=0.2)
        self.assertAlmostEqual(b["box"][2], 352, delta=0.2)
        self.assertEqual(boxes["c01"], [])

    def test_retangulo_da_legenda_respeita_posicao_e_zona_segura(self):
        base = T.caption_rect("Clique em Relatórios", "highlight", 1920, 1080, "bottom")
        topo = T.caption_rect("Clique em Relatórios", "highlight", 1920, 1080, "top")
        self.assertGreater(base[1], 1080 * 0.75)
        self.assertLess(topo[1] + topo[3], 1080 * 0.25)
        reels = T.caption_rect("Clique", "bold-pop", 1080, 1920, "bottom", "g", margin_px=480)
        self.assertLessEqual(reels[1] + reels[3], 1920 - 480)
        topo_reels = T.caption_rect("Clique", "bold-pop", 1080, 1920, "top", "g", top_px=326)
        self.assertGreaterEqual(topo_reels[1], 326)

    def test_reenquadrar_leva_o_foco_para_a_saida_e_descarta_o_que_saiu_do_recorte(self):
        g = T.output_geometry(1920, 1080, 1080, 1920, "reenquadrar", 0.14, 0.22)
        sb = {"meta": {"width": 1920, "height": 1080},
              "scenes": [{"id": "c1", "steps": [], "focus_boxes": [[900, 500, 120, 80], [10, 10, 100, 50]]}]}
        with tempfile.TemporaryDirectory() as d:
            save(Path(d) / "storyboard.json", sb)
            (box,) = T.output_focus_boxes(Path(d), sb, "reenquadrar", g, "9:16")["c1"]
        s = g["scale"]
        self.assertAlmostEqual(box["box"][0], (900 - g["x0"]) * s + g["ox"], delta=0.2)
        self.assertAlmostEqual(box["box"][1], 500 * s + g["y"], delta=0.2)


class Placement(Base):
    def test_smoke_real_fica_todo_na_base_e_passa(self):
        rep = audit(self.proj)
        self.assertEqual(rep.errors, [])
        self.assertTrue(all(c["position"] == "bottom" for c in self.placements()))

    def test_foco_embaixo_manda_so_os_blocos_daquela_cena_para_o_topo(self):
        self.target_at_bottom()
        placed = self.placements()
        c03 = [c for c in placed if c["scene"] == "c03"]
        outros = [c for c in placed if c["scene"] != "c03"]
        self.assertTrue(c03 and all(c["position"] == "top" for c in c03))
        self.assertTrue(all(c["position"] == "bottom" for c in outros))
        self.assertTrue(all(not c["collisions"] for c in placed))
        rep = audit(self.proj)
        self.assertEqual(rep.errors, [])
        self.assertTrue(any("fora da base" in w for w in rep.warnings))

    def test_ass_leva_o_override_de_posicao_por_bloco(self):
        self.target_at_bottom()
        sb = load(self.proj / "storyboard.json")
        cues = T.group_cues(T.project_words(self.proj, sb), 5, 3.4)
        ass = T.build_ass(cues, "highlight", 1920, 1080, "Segoe UI", "#4F46E5", "normal", "auto",
                          placements=self.placements())
        dialog = [l for l in ass.splitlines() if l.startswith("Dialogue:")]
        self.assertTrue(any("{\\an8}" in l for l in dialog))
        self.assertTrue(any("{\\an2}" in l for l in dialog))
        self.assertNotIn("\a", ass)

    def test_posicao_fixa_na_base_reprova_a_colisao(self):
        self.target_at_bottom()
        self.edit("tutorial.config.json", lambda c: c["captions"].update(position="bottom"))
        rep = audit(self.proj)
        self.assertTrue(rep.errors)
        self.assertTrue(all("c03" in e and "target_box s02" in e for e in rep.errors))
        self.assertIn("posição fixa", rep.errors[0])

    def test_caption_position_da_cena_vence_o_auto(self):
        self.edit("storyboard.json", lambda sb: sb["scenes"][1].update(caption_position="topo"))
        placed = self.placements()
        self.assertTrue(all(c["position"] == "top" for c in placed if c["scene"] == "c02"))

    def test_foco_em_cima_e_embaixo_vai_para_o_meio(self):
        self.edit("storyboard.json", lambda sb: sb["scenes"][2].update(
            focus_boxes=[[0, 0, 1920, 260], [0, 820, 1920, 260]]))
        placed = [c for c in self.placements() if c["scene"] == "c03"]
        self.assertTrue(all(c["position"] == "middle" and not c["collisions"] for c in placed))

    def test_sem_lugar_livre_reprova(self):
        self.edit("storyboard.json", lambda sb: sb["scenes"][2].update(focus_boxes=[[0, 0, 1920, 1080]]))
        rep = audit(self.proj)
        self.assertTrue(rep.errors)
        self.assertTrue(all("focus_boxes" in e for e in rep.errors))

    def test_saida_reels_e_auditada_no_quadro_dela(self):
        self.edit("tutorial.config.json", lambda c: c.update(saidas=[{
            "formato": "9:16", "resolucao": "1080p", "canal": "instagram-reels", "legenda": "bold-pop",
            "tamanho": "g", "seguro_topo": 0.14, "seguro_base": 0.22}]))
        rep = audit(self.proj)
        self.assertEqual(rep.errors, [])
        # foco no centro do mestre (dentro do recorte): livre no 16:9, mas no Reels reenquadrado cai
        # na faixa da legenda da base, e o topo do Reels (corpo g, várias linhas) cobre o seletor s02
        self.edit("storyboard.json", lambda sb: sb["scenes"][2].update(focus_boxes=[[860, 700, 200, 120]]))
        rep = audit(self.proj)
        self.assertTrue(rep.errors)
        self.assertTrue(all(e.startswith("9:16 1080p (instagram-reels) c03") for e in rep.errors))


@unittest.skipUnless(T.which("ffmpeg") and (SMOKE / "renders" / "smoke.raw.mp4").exists(), "ffmpeg ou render ausente")
class Burn(Base):
    def test_burn_grava_o_registro_de_posicoes(self):
        self.target_at_bottom()
        out = self.proj / "renders" / "smoke.mp4"
        args = SimpleNamespace(project=str(self.proj), style=None, input=str(SMOKE / "renders" / "smoke.raw.mp4"),
                               out=str(out), font=None, accent=None, case=None, position=None, size=None, lang=None)
        self.assertEqual(T.cmd_burn(args), 0)
        rec = load(out.with_suffix(".captions.json"))
        self.assertEqual(rec["position"], "auto")
        self.assertTrue(any(c["position"] == "top" for c in rec["cues"]))
        self.assertIn("{\\an8}", out.with_suffix(".ass").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
