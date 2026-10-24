"""Composição determinística (spec.json → vídeo), auditorias novas, estado e captura segura.

Rode: python tests/smoke/test_compose.py  (exige ffmpeg; nada vai à rede: a voz é simulada com words.json)
"""
from __future__ import annotations

import io
import json
import re
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

SMOKE = Path(__file__).resolve().parent
sys.path.insert(0, str(SMOKE.parent.parent / "aidd-skills" / "aidd-materialize-tutorial-stitch" / "scripts"))
import capture as CAP  # noqa: E402
import compose as C  # noqa: E402
import tutorial as T  # noqa: E402

BRAND = (":root { --brand-primary: #123456; --brand-accent: #0A0B0C; --brand-bg: #FFFFFF; --brand-text: #000000; }\n")


def quiet(fn, *a):
    with redirect_stdout(io.StringIO()):
        return fn(*a)


def png(path: Path, w: int, h: int) -> None:
    r = T.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"color=c=white:s={w}x{h}", "-frames:v", "1", str(path)],
              capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


SPEC = {
    "titulo": "Exportar a lista", "rota": "/painel", "auth": "atalho de teste; só observação", "publico": "consultores",
    "title_card": ["Exporte a", "lista", "CSV em um clique"], "outro_sub": "Agora você exporta a lista.",
    "imgs": {"home": "home.png", "depois": "depois.png"}, "first_img": "home",
    "caixas": {"csv": [1500, 300, 120, 60], "busca": [200, 300, 600, 60]},
    "steps": [{"id": "s01", "title": "Exportar", "user_action": "clicar em CSV", "result": "baixa o arquivo",
               "screen": "/painel", "img": "depois", "img_before": "home", "box": "csv", "ui_text": ["CSV"]}],
    "scenes": [
        {"id": "c01", "layout": "title", "title": "Abertura", "steps": [], "narration": "Neste tutorial, você exporta a lista.",
         "visual": "título", "camera": "fixa", "on_screen_text": ["Exporte"], "actions": []},
        {"id": "c02", "layout": "zoom-focus", "title": "Exportar", "steps": ["s01"],
         "narration": "Clique em CSV para baixar a lista.", "visual": "zoom no CSV", "camera": "zoom 1,4×",
         "on_screen_text": ["CSV"],
         "actions": [[0, "chip", "1", "Exportar"], [0, "focus", "csv", 1.4, 0.7], [0.3, "cursor", "csv", 0.6],
                     ["w:CSV", "click", "csv"], ["w:CSV+0.2", "show", "depois"],
                     ["w:baixar", "callout", "Arquivo gerado", "csv", "below", 1.5]]},
        {"id": "c03", "layout": "outro", "title": "Fecho", "steps": [], "narration": "Pronto. Agora você exporta a lista.",
         "visual": "check", "camera": "fixa", "on_screen_text": ["Pronto!"], "actions": []},
    ],
}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        prod = self.tmp / "produto"
        (prod / "02-marca" / "brand").mkdir(parents=True)
        (prod / "02-marca" / "brand" / "brand.css").write_text(BRAND, encoding="utf-8")
        png(prod / "02-marca" / "brand" / "logo.png", 300, 80)
        (prod / "catalogo.json").write_text(json.dumps({"produto": {"nome": "Produto X", "url": "https://app.exemplo.com",
                                                                    "marca": "Marca X"}, "tutoriais": []}), encoding="utf-8")
        self.proj = prod / "03-tutoriais" / "01-exportar"
        quiet(T.main, ["init", str(self.proj), "--idiomas", "pt-BR", "--gates", "nenhum"])
        png(self.proj / "evidence" / "home.png", 1920, 1600)
        png(self.proj / "evidence" / "depois.png", 1920, 1080)
        (self.proj / "spec.json").write_text(json.dumps(SPEC, ensure_ascii=False), encoding="utf-8")
        quiet(T.main, ["prepare", str(self.proj)])
        # voz simulada: palavras com tempos fixos (o tts real grava o mesmo formato)
        for sc in SPEC["scenes"]:
            ws, t = [], 0.2
            for w in sc["narration"].split():
                ws.append({"text": w, "start": round(t, 3), "end": round(t + 0.3, 3)})
                t += 0.35
            (self.proj / "audio" / f"{sc['id']}.words.json").write_text(json.dumps(ws), encoding="utf-8")
        sb = json.loads((self.proj / "storyboard.json").read_text(encoding="utf-8"))
        t = 0.0
        for s in sb["scenes"]:
            s["start"], s["end"] = round(t, 3), round(t + 5.0, 3)
            t += 5.0
        sb["meta"]["duration"] = t
        (self.proj / "storyboard.json").write_text(json.dumps(sb, ensure_ascii=False, indent=2), encoding="utf-8")
        r = T.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono", "-t", str(t),
                   str(self.proj / "audio" / "narration.wav")], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def compose(self):
        return quiet(T.main, ["compose", str(self.proj)])

    def audit(self, fn):
        rep = T.Report()
        fn(self.proj, rep)
        return rep


class Prepare(Base):
    def test_gera_roteiro_storyboard_stepmap_brief_e_esqueleto_sem_instrucoes_de_agente(self):
        p = self.proj
        self.assertIn("## c02 — Exportar  [steps: s01]", (p / "script.md").read_text(encoding="utf-8"))
        sm = json.loads((p / "step-map.json").read_text(encoding="utf-8"))
        self.assertEqual(sm["steps"][0]["target_box"], [1500, 300, 120, 60])
        self.assertEqual(sm["target"]["locator"], "https://app.exemplo.com/painel")
        self.assertIn("Produto X", (p / "brief.md").read_text(encoding="utf-8"))
        comp = p / "composition"
        for f in ("hyperframes.json", "package.json", "brand/brand.css", "assets/home.png", "assets/click.wav"):
            self.assertTrue((comp / f).exists(), f)
        # o esqueleto não leva AGENTS.md/CLAUDE.md: nenhuma harness puxa contexto extra ao abrir a pasta
        self.assertFalse((comp / "AGENTS.md").exists() or (comp / "CLAUDE.md").exists())

    def test_marca_sem_logo_e_recusada(self):
        shutil.rmtree(self.proj / "composition" / "brand")
        (self.proj.parents[1] / "02-marca" / "brand" / "logo.png").unlink()
        with self.assertRaisesRegex(C.ComposeError, "logo.png"):
            C.prepare(self.proj, T.project_config(self.proj), lambda out: None)

    def test_tamanho_de_imagem_sem_pil(self):
        self.assertEqual(C.img_size(self.proj / "evidence" / "home.png"), (1920, 1600))
        jpg = self.proj / "evidence" / "x.jpg"
        T.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=red:s=640x360", "-frames:v", "1", str(jpg)])
        self.assertEqual(C.img_size(jpg), (640, 360))


class Compose(Base):
    def test_composicao_completa_deterministica_e_auditada(self):
        self.assertEqual(self.compose(), 0)
        html = (self.proj / "composition" / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("{{", html)
        self.assertIn('alt="Marca X"', html)
        self.assertIn('stroke="#123456"', html)                    # cor da marca, não do Cadastros
        self.assertIn("app.exemplo.com/painel", html)
        # o clique acontece quando a narração diz "CSV" (palavra 3 da cena: 0.2 + 2 × 0.35)
        self.assertIn('click(', html)
        self.assertIn('at("c02", 0.900)', html)
        primeira = html
        self.compose()
        self.assertEqual((self.proj / "composition" / "index.html").read_text(encoding="utf-8"), primeira)
        rep = json.loads((self.proj / "composition" / "compose.json").read_text(encoding="utf-8"))
        self.assertEqual(rep["cenas"]["c02"]["cliques"][0]["palavra"], "w:CSV")
        self.assertEqual(rep["cenas"]["c02"]["sobreposicoes"][0]["tipo"], "callout")
        sb = json.loads((self.proj / "storyboard.json").read_text(encoding="utf-8"))
        self.assertTrue(sb["scenes"][1]["focus_boxes"])           # a legenda sabe onde não pode ficar

    def test_erros_dizem_o_que_corrigir(self):
        spec = json.loads((self.proj / "spec.json").read_text(encoding="utf-8"))
        spec["scenes"][1]["actions"].append(["w:Inexistente", "click", "csv"])
        (self.proj / "spec.json").write_text(json.dumps(spec), encoding="utf-8")
        with self.assertRaisesRegex(C.ComposeError, "Inexistente"):
            C.Composer(self.proj).build()
        spec["scenes"][1]["actions"][-1] = [1, "click", "csvv"]
        (self.proj / "spec.json").write_text(json.dumps(spec), encoding="utf-8")
        with self.assertRaisesRegex(C.ComposeError, "csv"):        # sugere a caixa parecida
            C.Composer(self.proj).build()
        spec["scenes"][1]["actions"][-1] = [1, "voar", "csv"]
        (self.proj / "spec.json").write_text(json.dumps(spec), encoding="utf-8")
        with self.assertRaisesRegex(C.ComposeError, "verbos"):
            C.Composer(self.proj).build()

    def test_override_entra_depois_das_acoes(self):
        ov = self.proj / "composition" / "overrides"
        ov.mkdir(parents=True)
        (ov / "c02.js").write_text('tl.to("#chip", { rotation: 2, duration: 0.2 }, at("c02", 1));', encoding="utf-8")
        self.compose()
        html = (self.proj / "composition" / "index.html").read_text(encoding="utf-8")
        self.assertIn("// override c02", html)
        self.assertLess(html.index("chip("), html.index("// override c02"))


class Audits(Base):
    def setUp(self):
        super().setUp()
        self.compose()
        self.html_f = self.proj / "composition" / "index.html"

    def test_composicao_limpa_passa(self):
        self.assertEqual(self.audit(T.audit_composition).errors, [])

    def test_pega_audio_sem_id_relogio_arquivo_faltando_e_timeline_velha(self):
        h = self.html_f.read_text(encoding="utf-8")
        h = h.replace('<audio id="sfx1"', '<audio', 1).replace("tl.seek(0);", "tl.seek(Math.random());")
        h = h.replace('src="assets/home.png"', 'src="assets/sumiu.png"')
        self.html_f.write_text(h, encoding="utf-8")
        sb = json.loads((self.proj / "storyboard.json").read_text(encoding="utf-8"))
        sb["scenes"][1]["end"] += 1
        (self.proj / "storyboard.json").write_text(json.dumps(sb), encoding="utf-8")
        errs = " | ".join(self.audit(T.audit_composition).errors)
        for frag in ("sem id", "Math.random", "sumiu.png", "timeline.js desatualizado"):
            self.assertIn(frag, errs)

    def test_pega_destaque_cobrindo_o_clique_e_fora_do_quadro(self):
        f = self.proj / "composition" / "compose.json"
        rep = json.loads(f.read_text(encoding="utf-8"))
        c = rep["cenas"]["c02"]
        c["sobreposicoes"].append({"tipo": "badge", "t0": 0.5, "t1": 2.0, "rect": c["cliques"][0]["rect"]})
        c["sobreposicoes"].append({"tipo": "callout", "t0": 3.0, "t1": 4.0, "rect": [1800, 1000, 300, 70]})
        f.write_text(json.dumps(rep), encoding="utf-8")
        errs = " | ".join(self.audit(T.audit_composition).errors)
        self.assertIn("cobre o elemento clicado", errs)
        self.assertIn("sai do quadro", errs)

    def test_privacidade(self):
        self.assertEqual(self.audit(T.audit_privacy).errors, [])
        (self.proj / "script.md").write_text("Fale com joao.silva@gmail.com ou (11) 98765-4321. "
                                             "Exemplo: maria@empresa.com, CPF 123.456.789-09.", encoding="utf-8")
        errs = " | ".join(self.audit(T.audit_privacy).errors)
        self.assertIn("joao.silva@gmail.com", errs)
        self.assertIn("98765-4321", errs)
        self.assertIn("123.456.789-09", errs)
        self.assertNotIn("maria@empresa.com", errs)              # fictício óbvio passa
        cfg = json.loads((self.proj / "tutorial.config.json").read_text(encoding="utf-8"))
        cfg["privacidade"] = {"permitidos": [r"joao\.silva@", r"98765", r"123\.456"]}
        (self.proj / "tutorial.config.json").write_text(json.dumps(cfg), encoding="utf-8")
        self.assertEqual(self.audit(T.audit_privacy).errors, [])

    def test_legenda_com_tempos_nao_vira_telefone(self):
        d = self.proj / "idiomas" / "en-US"
        d.mkdir(parents=True)
        (d / "legenda.vtt").write_text("WEBVTT\n\n00:00:10.000 --> 00:00:12.500\nClick CSV\n", encoding="utf-8")
        self.assertEqual(self.audit(T.audit_privacy).errors, [])


class Estado(Base):
    def test_fase_vem_do_disco_e_registro_nao_repete(self):
        quiet(T.main, ["estado", str(self.proj)])
        body = (self.proj / "ESTADO.md").read_text(encoding="utf-8")
        self.assertIn("- Fase atual: T4 roteiro e voz", body)      # sem narration.wav ainda
        self.assertIn("## Gates (histórico, anotado à mão)", body)   # a tabela do modelo vira histórico, não some
        T.registrar(self.proj, "igual")
        T.registrar(self.proj, "igual")
        quiet(T.main, ["estado", str(self.proj)])
        body = (self.proj / "ESTADO.md").read_text(encoding="utf-8")
        self.assertEqual(body.count("· igual"), 1)
        self.assertEqual(body.count("<!-- situação gerada"), 1)   # rodar de novo substitui o bloco


class Captura(unittest.TestCase):
    def test_recusa_acao_de_escrita_antes_de_abrir_o_navegador(self):
        r = {"base": "https://app.exemplo.com", "passos": [{"clicar": {"papel": "button", "nome": "Inativar usuário"}}]}
        with self.assertRaisesRegex(CAP.CaptureError, "grava dados"):
            CAP.capture(r, Path(tempfile.mkdtemp()), None)

    def test_regex_pega_o_caso_do_incidente(self):
        # o nome pedido era "Lista", mas o elemento real era "Inativar Analista Cadastro Teste"
        self.assertTrue(CAP.ACAO_PERIGOSA.search("Inativar Analista Cadastro Teste"))
        self.assertFalse(CAP.ACAO_PERIGOSA.search("Visualização em Lista"))


class Revisao(Base):
    """Achados da revisão adversarial: cada um vira teste."""

    def test_end_d_e_antes_do_fim(self):
        c = C.Composer(self.proj)
        self.assertAlmostEqual(c.when("c02", "end-0.5"), 4.5)
        self.assertAlmostEqual(c.when("c02", "end"), 5.0)
        with self.assertRaises(C.ComposeError):
            c.when("c02", "end0.5")

    def test_palavra_com_hifen_e_numero_e_ancora_vazia(self):
        ws = [{"text": "Use", "start": 0.2, "end": 0.4}, {"text": "COVID-19", "start": 0.6, "end": 1.0},
              {"text": "E-mail", "start": 1.2, "end": 1.5}, {"text": "e-mail", "start": 2.0, "end": 2.3}]
        (self.proj / "audio" / "c02.words.json").write_text(json.dumps(ws), encoding="utf-8")
        c = C.Composer(self.proj)
        self.assertAlmostEqual(c.when("c02", "w:COVID-19"), 0.6)
        self.assertAlmostEqual(c.when("c02", "w:E-mail#2+0.1"), 2.1)   # o deslocamento não se perde
        self.assertAlmostEqual(c.when("c02", "w:Use+0.3"), 0.5)
        with self.assertRaisesRegex(C.ComposeError, "palavra"):
            c.when("c02", "w:%")

    def test_texto_da_spec_e_escapado(self):
        spec = json.loads((self.proj / "spec.json").read_text(encoding="utf-8"))
        spec["title_card"] = ["Exporte <b>já</b>", "a lista & mais", "CSV"]
        spec["scenes"][1]["actions"][-1] = ["w:baixar", "callout", "<i>x</i>", "csv", "below", 1.5]
        (self.proj / "spec.json").write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
        self.compose()
        h = (self.proj / "composition" / "index.html").read_text(encoding="utf-8")
        self.assertIn("Exporte &lt;b&gt;já&lt;/b&gt;", h)
        self.assertIn("a lista &amp; mais", h)
        self.assertNotIn("<i>x</i>", h)

    def test_capturas_de_larguras_diferentes_sao_recusadas(self):
        png(self.proj / "evidence" / "depois.png", 1280, 720)
        with self.assertRaisesRegex(C.ComposeError, "larguras"):
            C.Composer(self.proj)

    def test_jpeg_truncado_vira_erro_claro(self):
        f = self.proj / "evidence" / "t.jpg"
        f.write_bytes(bytes((0xFF, 0xD8, 0xFF, 0xFF, 0xE0, 0x00)))
        with self.assertRaises(C.ComposeError):
            C.img_size(f)

    def test_estado_guarda_gates_e_fase_anotados_e_nao_embaralha_secoes(self):
        e = self.proj / "ESTADO.md"
        linhas = ["# Estado do tutorial", "", "- Projeto: x", "- Fase atual: T8 (gates: nenhum, decisão do usuário)", "",
                  "## Gates", "| Gate | Status | Data | Observação |", "|---|---|---|---|", "| P6 aceite | pendente | | revisão |", "",
                  "## Registro de decisões", "- 2026-10-20 · a", "  continuação de a", "- 2026-10-21 · b", "- 2026-10-22 · a", "",
                  "## Pendências do usuário", "- revisar narração", ""]
        e.write_text(chr(10).join(linhas), encoding="utf-8")
        quiet(T.main, ["estado", str(self.proj)])
        quiet(T.main, ["estado", str(self.proj)])
        body = e.read_bytes().decode("utf-8")
        self.assertNotIn(chr(13), body)
        self.assertIn("decisão do usuário", body)                         # o que a pessoa escreveu fica
        self.assertIn("| P6 aceite | pendente | | revisão |", body)
        reg = body.split("## Registro de decisões")[1].split("## Pendências")[0]
        self.assertEqual(reg.count("· a"), 1)
        self.assertIn("2026-10-22 · a" + chr(10) + "  continuação de a", reg)   # continuação segue a sua linha
        self.assertEqual(body.split("## Pendências do usuário")[1].strip(), "- revisar narração")

    def test_privacidade_casos_da_revisao(self):
        ruido = "logo@2x.png gsap@3.14.2 das 08 0800-1800 build 10 2026 1022 5511900000001 00:00:10.000 --> 00:00:12.500"
        real = "11987654321 (11) 9 8765-4321 12345678909 joao0000@gmail.com 11222333000181"
        (self.proj / "script.md").write_text(ruido, encoding="utf-8")
        self.assertEqual(self.audit(T.audit_privacy).errors, [])
        (self.proj / "script.md").write_text(real, encoding="utf-8")
        errs = " | ".join(self.audit(T.audit_privacy).errors)
        for v in ("11987654321", "8765-4321", "12345678909", "joao0000@gmail.com", "11222333000181"):
            self.assertIn(v, errs)

    def test_privacidade_le_override_e_traducao(self):
        ov = self.proj / "composition" / "overrides"
        ov.mkdir(parents=True)
        (ov / "c02.js").write_text('tl.set("#x", { textContent: "ana.real@gmail.com" }, 0);', encoding="utf-8")
        d = self.proj / "idiomas" / "es"
        d.mkdir(parents=True)
        (d / "traducao.json").write_text('{"cenas": [{"texto": "Llame al (11) 98765-4321"}]}', encoding="utf-8")
        errs = " | ".join(self.audit(T.audit_privacy).errors)
        self.assertIn("ana.real@gmail.com", errs)
        self.assertIn("98765-4321", errs)

    def test_produzir_recusa_ordem_invertida(self):
        with self.assertRaises(SystemExit):
            quiet(T.main, ["produzir", str(self.proj), "--de", "render", "--ate", "tts"])


class CapturaSegura(unittest.TestCase):
    def test_lista_do_que_e_permitido(self):
        bloqueia = ["Desativar", "Ativar", "Cadastrar", "Cancelar", "Atualizar status", "Mover para Aprovado", "Bloquear",
                    "Arquivar", "Convidar", "Sim", "OK", "Delete", "Save", "Submit", "", "Inativar Analista Cadastro Teste",
                    "Algo desconhecido"]
        libera = ["Visualização em Lista", "Fila Operacional", "Relatórios & Métricas", "A-Z", "Z-A", "7D", "Próxima",
                  "Anterior", "Visualizar Detalhes", "Limpar todos", "Todos os status", "Ver pendentes", "Cards", "Kanban"]
        for t in bloqueia:
            self.assertFalse(CAP.clique_seguro({"texto": t, "papel": "button"})[0], t)
        for t in libera:
            self.assertTrue(CAP.clique_seguro({"texto": t, "papel": "button"})[0], t)
        self.assertTrue(CAP.clique_seguro({"texto": "Templates", "papel": "a", "href": "/templates"})[0])
        self.assertFalse(CAP.clique_seguro({"texto": "Sair", "papel": "a", "href": "/logout"})[0])
        self.assertFalse(CAP.ACAO_PERIGOSA.search("Renovação"))
        # cada rótulo conta: navegação no aria-label libera; escrita em qualquer rótulo bloqueia
        self.assertTrue(CAP.clique_seguro({"rotulos": ["Lista", "Visualização em Lista"], "papel": "button"})[0])
        self.assertFalse(CAP.clique_seguro({"rotulos": ["Lista", "Inativar Analista Cadastro Teste"], "papel": "button"})[0])

    def test_roteiro_recusa_ir_e_selecionar_perigosos(self):
        for passo in ({"ir": "/logout"}, {"ir": "/clientes/9/excluir"},
                      {"selecionar": {"papel": "combobox", "nome": "Situação do cliente 9"}, "opcao": "Reprovado"}):
            with self.assertRaises(CAP.CaptureError):
                CAP.checar_roteiro({"passos": [passo]})
        CAP.checar_roteiro({"passos": [{"selecionar": {"papel": "combobox", "nome": "Status"}, "opcao": "Aprovados"},
                                       {"ir": "/templates"}]})


if __name__ == "__main__":
    unittest.main(verbosity=2)
