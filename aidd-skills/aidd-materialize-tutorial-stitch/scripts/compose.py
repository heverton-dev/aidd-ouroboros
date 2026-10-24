"""Composição determinística de um tutorial a partir de spec.json (T5–T7 sem HTML escrito à mão).

O agente escreve só <tutorial>/spec.json: passos, narração e as ações de cada cena. Daqui saem
  prepare  → script.md, step-map.json, storyboard.json (tempos provisórios), brief.md e o esqueleto de composition/
  compose  → composition/index.html completo (câmera, rolagem, cursor, cliques, destaques, digitação, trocas de tela),
             screen_box/focus_boxes no storyboard, target_box no step-map e composition/compose.json (auditorias)
Os tempos vêm da voz medida (audio/<cena>.words.json): uma ação "w:Gerar" acontece quando a narração diz "Gerar".
Motor nascido em cadastros-conexao/04-geradores (build.py), sem nada fixo de um produto.

Formato do spec.json (references/07b-compose.md):
  titulo, perfil, publico, rota, auth           texto do brief/step-map; rota completa a URL do catálogo
  title_card [linha1, linha2 (cor da marca), subtítulo]      outro_sub   texto do fecho
  imgs {chave: arquivo em evidence/}  first_img              caixas {nome: [x,y,w,h]} (opcional)
  steps [{id,title,user_action,result,screen,img,img_before?,box,ui_text,sensitive?,notes?}]
  scenes [{id,layout,title,steps,narration,visual,camera,on_screen_text,extra?,actions:[[quando, verbo, ...]]}]
Caixas: "<captura>:<elemento>" de evidence/boxes.json (tutorial.py capture), nome de "caixas" ou [x,y,w,h] em pixels
da captura. Quando: segundos desde o início da cena, "w:Palavra[#n][+/-d]" ou "end-d".
"""
from __future__ import annotations

import difflib
import html
import json
import re
import shutil
import struct
import unicodedata
from pathlib import Path

HOME = Path(__file__).resolve().parent.parent
TPL = HOME / "templates" / "compose"

WX, WY, BAR, VW, VH = 320, 110, 40, 1280, 720   # janela do app no quadro 1920x1080 (CSS px)
OVERSCROLL = 360    # rolar além do fim da captura mostra o fundo do app, para subir conteúdo baixo
CHAR_W = 17         # largura média de um caractere a 30 px/600 (Inter), para medir etiquetas
WPS = 2.5           # palavras por segundo dos tempos provisórios (a voz medida manda depois)
VERBOS = ("focus", "scroll", "cursor", "click", "spot", "callout", "badge", "type", "hide", "show", "chip")
PRONTO = {"pt": "Pronto!", "en": "Done!", "es": "¡Listo!"}


class ComposeError(Exception):
    pass


def detect_scene_engine(scene: dict) -> str:
    """Identifica se a cena utiliza o motor conceitual Remotion ou Playwright."""
    engine = scene.get("engine", "").lower()
    layout = scene.get("layout", "").lower()
    if engine == "remotion" or layout in ("animacao_conceitual", "remotion", "diagram"):
        return "remotion"
    return "playwright"


def build_remotion_render_command(
    entry_point: Path,
    composition_id: str,
    out_file: Path,
    fps: int = 60,
    props_file: Path | None = None,
) -> list[str]:
    """Monta o comando determinístico de render do Remotion."""
    cmd = [
        "npx",
        "remotion",
        "render",
        str(entry_point).replace("\\", "/"),
        composition_id,
        str(out_file).replace("\\", "/"),
        "--fps",
        str(fps),
    ]
    if props_file and props_file.exists():
        cmd.extend(["--props", str(props_file).replace("\\", "/")])
    return cmd


def generate_ffmpeg_concat_file(video_paths: list[Path], out_file: Path) -> Path:
    """Gera a lista formatada para concatenação demuxer do FFmpeg."""
    out_file = Path(out_file)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for vp in video_paths:
        vp_path = Path(vp)
        if vp_path.parent == out_file.parent:
            filename = vp_path.name
        else:
            filename = str(vp_path.resolve()).replace("\\", "/")
        lines.append(f"file '{filename}'")
    out_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_file


def norm(s: str) -> str:
    s = unicodedata.normalize("NFC", s.lower())
    return re.sub(r"[^\w\-]", "", s)


def r1(v: float) -> float:
    return round(v, 1)


def img_size(p: Path) -> tuple[int, int]:
    """Largura e altura de PNG (cabeçalho IHDR) ou JPEG (marcador SOF), só com a biblioteca padrão."""
    b = p.read_bytes()
    if b[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", b[16:24])
    if b[:2] == bytes((0xFF, 0xD8)):
        i = 2
        while i + 9 <= len(b):
            if b[i] != 0xFF:
                i += 1
                continue
            m = b[i + 1]
            if m == 0xFF:          # bytes de preenchimento entre marcadores
                i += 1
                continue
            if m in (0xC0, 0xC1, 0xC2):
                h, w = struct.unpack(">HH", b[i + 5:i + 9])
                return w, h
            if m in (0xD8, 0x01) or 0xD0 <= m <= 0xD7:   # marcadores sem tamanho
                i += 2
                continue
            i += 2 + struct.unpack(">H", b[i + 2:i + 4])[0]
    raise ComposeError(f"não reconheço o formato de {p} (PNG ou JPEG íntegro)")


def load(p: Path):
    return json.loads(p.read_text(encoding="utf-8-sig"))


def find_up(start: Path, rels: tuple[str, ...], depth: int = 5) -> Path | None:
    p = start.resolve()
    for _ in range(depth):
        for r in rels:
            if (p / r).exists():
                return p / r
        p = p.parent
    return None


def product_info(proj: Path) -> dict:
    """Dados do produto que valem para todo tutorial: o catálogo (nome, url, marca) e a pasta da marca."""
    cat_f = find_up(proj.parent, ("catalogo.json",))
    prod = load(cat_f).get("produto", {}) if cat_f else {}
    brand = find_up(proj.parent, ("02-marca/brand/brand.css", "compartilhado/brand/brand.css", "marca/brand/brand.css"))
    return {"nome": prod.get("nome", ""), "url": prod.get("url", ""), "marca": prod.get("marca") or prod.get("nome", ""),
            "brand_dir": brand.parent if brand else None, "catalogo": cat_f}


def hex_rgba(h: str, a: float) -> str:
    h = h.lstrip("#")
    return f"rgba({int(h[0:2], 16)}, {int(h[2:4], 16)}, {int(h[4:6], 16)}, {a})"


def brand_color(css: str, name: str, default: str) -> str:
    m = re.search(rf"--brand-{name}\s*:\s*(#[0-9a-fA-F]{{6}})", css)
    return m.group(1).upper() if m else default


class Composer:
    def __init__(self, proj: Path):
        self.proj = proj
        f = proj / "spec.json"
        if not f.exists():
            raise ComposeError(f"{f} não existe (o agente escreve só esse arquivo; ver references/07b-compose.md)")
        self.T = load(f)
        self.sb = load(proj / "storyboard.json")
        self.sm = load(proj / "step-map.json")
        self.S = {s["id"]: s for s in self.sb["scenes"]}
        self.prod = product_info(proj)
        boxes_f = proj / "evidence" / "boxes.json"
        self.H = dict(load(boxes_f)) if boxes_f.exists() else {}
        self.H.update(self.T.get("caixas") or {})
        self.imgs = dict(self.T["imgs"])
        self.order = list(self.imgs)
        sizes = {}
        for k, v in self.imgs.items():
            p = proj / "evidence" / v
            if not p.exists():
                raise ComposeError(f"imagem '{k}' não encontrada: {p}")
            sizes[k] = img_size(p)
        self.ih = {k: s[1] for k, s in sizes.items()}
        larguras = {s[0] for s in sizes.values()}
        if len(larguras) > 1:   # todas as telas na mesma escala, senão as caixas desalinham
            raise ComposeError(f"capturas com larguras diferentes ({sorted(larguras)}): capture todas no mesmo viewport e escala")
        # escala captura → janela: a captura de 1280 CSS px a 1,5x (1920 px) cabe nos 1280 px da janela (K = 2/3)
        self.K = VW / sizes[self.T["first_img"]][0]
        self.f, self.s, self.sy, self.img = (640.0, 400.0), 1.0, 0.0, self.T["first_img"]
        self.js, self.html, self.audio, self.fields, self.html_fields = [], [], [], {}, []
        self.fb = {sid: [] for sid in self.S}
        self.snap, self.n, self.chip_on, self.focus_same_time = {}, 0, False, False
        self.report = {sid: {"cliques": [], "sobreposicoes": [], "acoes": 0} for sid in self.S}

    # ---------------------------------------------------------------- geometria
    def box(self, b):
        if isinstance(b, str):
            if b not in self.H:
                perto = difflib.get_close_matches(b, list(self.H), n=3)
                raise ComposeError(f"caixa '{b}' desconhecida" + (f" (quis dizer {', '.join(perto)}?)" if perto else
                                                                  " (meça com tutorial.py capture ou declare em 'caixas')"))
            return list(self.H[b])
        return list(b)

    def loc(self, cx, cy):
        return (cx * self.K, cy * self.K + BAR - self.sy * self.K)

    def ctr(self, b):
        return self.loc(b[0] + b[2] / 2, b[1] + b[3] / 2)

    def scr(self, q):
        return (WX + self.f[0] * (1 - self.s) + q[0] * self.s, WY + self.f[1] * (1 - self.s) + q[1] * self.s)

    def rect(self, b):
        x, y = self.scr(self.loc(b[0], b[1]))
        return [x, y, b[2] * self.K * self.s, b[3] * self.K * self.s]

    # ---------------------------------------------------------------- tempo
    def words(self, sid):
        p = self.proj / "audio" / f"{sid}.words.json"
        return load(p) if p.exists() else []

    def when(self, sid, t):
        sc = self.S[sid]
        if isinstance(t, (int, float)):
            return float(t)
        if t.startswith("end"):
            m = re.match(r"end([+-]\d+(?:\.\d+)?)?$", t)
            if not m:
                raise ComposeError(f"{sid}: tempo '{t}' inválido (use 'end' ou 'end-0.5')")
            return (sc["end"] - sc["start"]) + float(m.group(1) or 0)   # "end-0.5" = meio segundo antes do fim
        m = re.match(r"w:([^#]+?)(?:#(\d+))?([+-]\d+(?:\.\d+)?)?$", t)
        if not m:
            raise ComposeError(f"{sid}: tempo '{t}' inválido (use número, 'w:Palavra[#n][+/-d]' ou 'end-d')")
        ws = self.words(sid)
        raw, nth, d = m.group(1), int(m.group(2) or 1), float(m.group(3) or 0)
        # palavra com hífen e número ("COVID-19") vence a leitura como deslocamento quando existe na fala
        whole = t[2:]
        if m.group(3) and "#" not in whole and any(norm(w["text"]) == norm(whole) for w in ws):
            raw, d = whole, 0.0
        tok = norm(raw)
        if not tok:
            raise ComposeError(f"{sid}: '{t}' não tem palavra depois de 'w:'")
        hits = [w for w in ws if norm(w["text"]) == tok] or [w for w in ws if norm(w["text"]).startswith(tok)]
        if len(hits) < nth:
            raise ComposeError(f"{sid}: palavra '{m.group(1)}' (#{nth}) não está na narração medida "
                               f"(rode tts/retime antes; palavras: {' '.join(w['text'] for w in ws[:14])}…)")
        return max(0.0, hits[nth - 1]["start"] + d)

    def at(self, sid, off):
        return f'at("{sid}", {off:.3f})'

    def sfx(self, sid, off, name, dur, vol):
        self.n += 1
        self.audio.append(f'<audio id="sfx{self.n}" src="assets/{name}.wav" data-scene="{sid}" data-offset="{off:.3f}" '
                          f'data-start="0" data-duration="{dur}" data-volume="{vol}" data-track-index="{9 + self.n}"></audio>')

    def add_fb(self, sid, r, pad=0):
        self.fb[sid].append([r1(r[0] - pad), r1(r[1] - pad), r1(r[2] + 2 * pad), r1(r[3] + 2 * pad)])

    def overlay(self, sid, off, dur, r, tipo):
        self.report[sid]["sobreposicoes"].append({"tipo": tipo, "t0": round(off, 3), "t1": round(off + dur, 3),
                                                  "rect": [r1(v) for v in r]})

    # ---------------------------------------------------------------- ações
    def a_focus(self, sid, off, target, s, d):
        q = (640.0, 400.0) if target == "center" else self.ctr(self.box(target))
        self.js.append(f'tl.to("#win", {{ x: {r1(q[0] * (1 - s))}, y: {r1(q[1] * (1 - s))}, scale: {s}, duration: {d}, ease: "expo.inOut" }}, {self.at(sid, off)});')
        self.f, self.s = q, s

    def a_scroll(self, sid, off, sy, d):
        sy = max(0.0, min(float(sy), self.ih[self.img] - VH / self.K + OVERSCROLL))
        # a âncora da câmera acompanha a rolagem para o foco continuar no mesmo ponto da página
        self.f = (self.f[0], self.f[1] - (sy - self.sy) * self.K) if self.s != 1 else self.f
        if self.s != 1 and not self.focus_same_time:
            self.js.append(f'tl.to("#win", {{ x: {r1(self.f[0] * (1 - self.s))}, y: {r1(self.f[1] * (1 - self.s))}, duration: {d}, ease: "power2.inOut" }}, {self.at(sid, off)});')
        self.js.append(f'tl.to("#page", {{ y: {r1(-sy * self.K)}, duration: {d}, ease: "power2.inOut" }}, {self.at(sid, off)});')
        self.sy = sy

    def a_cursor(self, sid, off, target, d):
        x, y = self.scr(self.ctr(self.box(target)))
        self.js.append(f'tl.to("#cursor", {{ x: {r1(x - 6)}, y: {r1(y - 4)}, duration: {d}, ease: "power3.inOut" }}, {self.at(sid, off)});')

    def a_click(self, sid, off, target):
        b = self.box(target)
        x, y = self.scr(self.ctr(b))
        self.snap[tuple(b)] = (self.f, self.s, self.sy)
        self.js.append(f'click({r1(x)}, {r1(y)}, {self.at(sid, off)});')
        self.sfx(sid, off, "click", 0.04, 0.9)
        self.report[sid]["cliques"].append({"t": round(off, 3), "rect": [r1(v) for v in self.rect(b)],
                                            "palavra": None})

    def a_spot(self, sid, off, target, dur):
        b = self.box(target)
        self.snap.setdefault(tuple(b), (self.f, self.s, self.sy))
        r = self.rect(b)
        self.n += 1
        el = f"spot{self.n}"
        self.html.append(f'<div id="{el}" class="spot" style="left:{r1(r[0] - 7)}px;top:{r1(r[1] - 7)}px;width:{r1(r[2] + 14)}px;height:{r1(r[3] + 14)}px"></div>')
        self.js.append(f'tl.fromTo("#{el}", {{ opacity: 0, scale: 1.04 }}, {{ opacity: 1, scale: 1, duration: 0.3, ease: "power2.out", immediateRender: false }}, {self.at(sid, off)});')
        self.js.append(f'tl.to("#{el}", {{ opacity: 0, duration: 0.25 }}, {self.at(sid, off + dur)});')
        self.add_fb(sid, r, 9)

    def label_pos(self, r, w, h, side):
        if side == "below":
            x, y = r[0] + r[2] / 2 - w / 2, r[1] + r[3] + 22
        elif side == "above":
            x, y = r[0] + r[2] / 2 - w / 2, r[1] - 22 - h
        elif side == "left":
            x, y = r[0] - 24 - w, r[1] + r[3] / 2 - h / 2
        else:
            x, y = r[0] + r[2] + 24, r[1] + r[3] / 2 - h / 2
        return max(340.0, min(x, 1580.0 - w)), y

    def a_callout(self, sid, off, text, target, side, dur):
        r = self.rect(self.box(target))
        w, h = len(text) * CHAR_W + 48, 68
        x, y = self.label_pos(r, w, h, side)
        self.n += 1
        el = f"co{self.n}"
        self.html.append(f'<div id="{el}" class="callout" style="left:{r1(x)}px;top:{r1(y)}px">{html.escape(text)}</div>')
        self.js.append(f'tl.fromTo("#{el}", {{ opacity: 0, y: 14 }}, {{ opacity: 1, y: 0, duration: 0.45, ease: "back.out(1.8)", immediateRender: false }}, {self.at(sid, off)});')
        self.js.append(f'tl.to("#{el}", {{ opacity: 0, duration: 0.3 }}, {self.at(sid, off + dur)});')
        self.sfx(sid, off, "pop", 0.28, 0.4)
        self.add_fb(sid, [x, y, w, h], 6)
        self.overlay(sid, off, dur, [x, y, w, h], "callout")

    def a_badge(self, sid, off, text, icon, target, side, dur):
        r = self.rect(self.box(target))
        w, h = len(text) * CHAR_W + 110, 76
        x, y = self.label_pos(r, w, h, side)
        self.n += 1
        el = f"badge{self.n}"
        self.html.append(f'<div id="{el}" class="badge" style="left:{r1(x)}px;top:{r1(y)}px"><i>{html.escape(icon)}</i>{html.escape(text)}</div>')
        self.js.append(f'tl.fromTo("#{el}", {{ opacity: 0, y: 16 }}, {{ opacity: 1, y: 0, duration: 0.45, ease: "back.out(1.8)", immediateRender: false }}, {self.at(sid, off)});')
        self.js.append(f'tl.to("#{el}", {{ opacity: 0, duration: 0.3 }}, {self.at(sid, off + dur)});')
        self.sfx(sid, off, "pop", 0.28, 0.45)
        self.add_fb(sid, [x, y, w, h], 6)
        self.overlay(sid, off, dur, [x, y, w, h], "badge")

    def a_type(self, sid, off, fid, target, text, cps, padx):
        b = self.box(target)
        K = self.K
        if fid not in self.fields:
            self.fields[fid] = b
            self.html_fields.append(
                f'<div id="f-{fid}" class="field" data-layout-ignore style="left:{r1(b[0] * K + 3)}px;top:{r1(b[1] * K + 3)}px;'
                f'width:{r1(b[2] * K - 6)}px;height:{r1(b[3] * K - 6)}px;padding-left:{r1(padx * K - 3)}px">'
                f'<span id="t-{fid}"></span><i class="caret" id="k-{fid}"></i></div>')
        self.js.append(f'tl.set("#f-{fid}", {{ opacity: 1 }}, {self.at(sid, off)});')
        for i in range(1, len(text) + 1):
            self.js.append(f'tl.set("#t-{fid}", {{ textContent: {json.dumps(text[:i], ensure_ascii=False)} }}, {self.at(sid, off + i / cps)});')
        if text:
            self.js.append(f'tl.set("#k-{fid}", {{ opacity: 0 }}, {self.at(sid, off + len(text) / cps + 0.5)});')
        else:
            self.js.append(f'tl.set("#k-{fid}", {{ opacity: 0 }}, {self.at(sid, off)});')

    def a_hide(self, sid, off, fid):
        self.js.append(f'tl.set("#f-{fid}", {{ opacity: 0 }}, {self.at(sid, off)});')

    def a_show(self, sid, off, key):
        if key not in self.imgs:
            raise ComposeError(f"{sid}: show '{key}' não está em imgs ({', '.join(self.imgs)})")
        new, old = self.order.index(key), self.order.index(self.img)
        if key == self.img:
            return
        if new > old:
            self.js.append(f'tl.to("#img-{key}", {{ opacity: 1, duration: 0.3 }}, {self.at(sid, off)});')
            self.js.append(f'tl.set("#img-{self.img}", {{ opacity: 0 }}, {self.at(sid, off + 0.32)});')
        else:
            self.js.append(f'tl.set("#img-{key}", {{ opacity: 1 }}, {self.at(sid, off)});')
            self.js.append(f'tl.to("#img-{self.img}", {{ opacity: 0, duration: 0.3 }}, {self.at(sid, off)});')
        self.img = key
        maxsy = max(0.0, self.ih[key] - VH / self.K + OVERSCROLL)
        if self.sy > maxsy:
            self.a_scroll(sid, off, maxsy, 0.3)

    def a_chip(self, sid, off, n, text):
        self.js.append(f'chip({json.dumps(n)}, {json.dumps(text, ensure_ascii=False)}, {self.at(sid, off)}, {str(not self.chip_on).lower()});')
        self.chip_on = True

    # ---------------------------------------------------------------- montagem
    def build(self) -> dict:
        T, scenes = self.T, self.sb["scenes"]
        spec_ids = [s["id"] for s in T["scenes"]]
        if spec_ids != [s["id"] for s in scenes]:
            raise ComposeError(f"cenas da spec {spec_ids} ≠ storyboard {[s['id'] for s in scenes]} (rode tutorial.py prepare)")
        tl_len = scenes[0]["end"] - scenes[0]["start"]
        self.sfx(scenes[0]["id"], tl_len - 0.95, "whoosh", 0.55, 0.45)
        self.sfx(scenes[-1]["id"], -0.35, "whoosh", 0.55, 0.45)
        self.sfx(scenes[-1]["id"], 0.55, "pop", 0.28, 0.5)
        stage = [s for s in scenes if s["layout"] not in ("title", "outro")]
        if not stage:
            raise ComposeError("nenhuma cena de palco (só title/outro)")
        first, last = stage[0]["id"], stage[-1]["id"]
        title_id, outro_id = scenes[0]["id"], scenes[-1]["id"]
        chip_text = {}
        for spec in T["scenes"]:
            sid = spec["id"]
            for a in spec.get("actions", []):
                if len(a) < 2 or a[1] not in VERBOS:
                    raise ComposeError(f"{sid}: ação {a!r} — verbos: {', '.join(VERBOS)}")
            acts = sorted(((self.when(sid, a[0]), i, a) for i, a in enumerate(spec.get("actions", []))),
                          key=lambda x: (x[0], x[1]))
            if spec["layout"] not in ("title", "outro") and sid == first:
                self.js.append(f'tl.to("#cursor", {{ opacity: 1, duration: 0.3 }}, {self.at(sid, 0.3)});')
            for j, (off, _, a) in enumerate(acts):
                self.focus_same_time = any(b[2][1] == "focus" and abs(b[0] - off) < 1e-6 for b in acts[j + 1:])
                try:
                    getattr(self, "a_" + a[1])(sid, off, *a[2:])
                except TypeError as e:
                    raise ComposeError(f"{sid}: argumentos de {a[1]} errados em {a!r} ({e})") from None
                if a[1] == "click" and isinstance(a[0], str) and a[0].startswith("w:"):
                    self.report[sid]["cliques"][-1]["palavra"] = a[0]
                if a[1] == "chip":
                    chip_text[sid] = a[3]
            self.report[sid]["acoes"] = len(acts)
            # chip visível nesta cena → área protegida da legenda
            if self.chip_on and spec["layout"] not in ("title", "outro"):
                txt = chip_text.get(sid) or next(reversed(chip_text.values()))
                self.add_fb(sid, [WX, 34, 46 + 14 + 32 + 10 + len(txt) * CHAR_W, 66], 4)
            # estado da câmera no fim da cena: screen_box e target_box no viewport
            sc = self.S[sid]
            for st in sc.get("steps", []):
                step = next((x for x in self.sm["steps"] if x["id"] == st), None)
                spec_step = next((x for x in T["steps"] if x["id"] == st), None)
                if not step or not spec_step:
                    raise ComposeError(f"{sid}: passo '{st}' não está no step-map/spec (rode tutorial.py prepare)")
                pb = self.box(spec_step["box"])
                f, s, sy = self.snap.get(tuple(pb), (self.f, self.s, self.sy))
                f0, s0, sy0 = self.f, self.s, self.sy
                self.f, self.s, self.sy = f, s, sy
                x0, y0 = self.scr((0.0, BAR))
                sc["screen_box"] = [r1(x0), r1(y0), r1(VW * s), r1(VH * s)]
                step["target_box"] = [pb[0], round(pb[1] - sy), pb[2], pb[3]]
                self.f, self.s, self.sy = f0, s0, sy0
            sc["zoom"] = 1.0
            sc["focus_boxes"] = self.fb[sid]
        self.sb["meta"]["screen_box"] = [WX, WY + BAR, VW, VH]
        (self.proj / "storyboard.json").write_text(json.dumps(self.sb, ensure_ascii=False, indent=2), encoding="utf-8")
        (self.proj / "step-map.json").write_text(json.dumps(self.sm, ensure_ascii=False, indent=1), encoding="utf-8")
        self.write_html(title_id, outro_id, first, last)
        rep = {"versao": 1, "verbos": VERBOS, "cenas": self.report,
               "overrides": sorted(p.name for p in (self.proj / "composition" / "overrides").glob("*") if p.is_file())
               if (self.proj / "composition" / "overrides").exists() else []}
        (self.proj / "composition" / "compose.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
        return {"comandos": len(self.js), "sobreposicoes": len(self.html), "sons": len(self.audio)}

    def write_html(self, title_id, outro_id, first, last):
        T = self.T
        dur = self.sb["meta"]["duration"]
        l1, l2, sub = T["title_card"]
        imgs = "\n          ".join(
            f'<img id="img-{k}" class="shot" src="assets/{v}" alt=""{"" if k == T["first_img"] else " style=\"opacity:0\""} />'
            for k, v in self.imgs.items())
        comp = self.proj / "composition"
        css = (comp / "brand" / "brand.css").read_text(encoding="utf-8") if (comp / "brand" / "brand.css").exists() else ""
        primary, accent = brand_color(css, "primary", "#00568F"), brand_color(css, "accent", "#0284C7")
        lang = self.sb["meta"].get("language", "pt-BR")
        url = T.get("url") or self.prod["url"]
        host = re.sub(r"^https?://", "", url).rstrip("/")
        # encaixes de animação feita à mão: composition/overrides/<cena>.js entra depois das ações geradas
        ov_dir, overrides = comp / "overrides", []
        for spec in T["scenes"]:
            jsf, htf = ov_dir / f"{spec['id']}.js", ov_dir / f"{spec['id']}.html"
            if htf.exists():
                self.html.append(f"<!-- override {spec['id']} -->\n" + htf.read_text(encoding="utf-8").strip())
            if jsf.exists():
                overrides.append(f"      // override {spec['id']} (overrides/{jsf.name})\n" + jsf.read_text(encoding="utf-8").rstrip())
        tpl = (TPL / "stage.html").read_text(encoding="utf-8")
        vals = {"DUR": str(dur), "TITLE_ID": title_id, "OUTRO_ID": outro_id, "FIRST": first, "LAST": last,
                "L1": html.escape(l1), "L2": html.escape(l2), "SUB": html.escape(sub), "OUTRO_SUB": html.escape(T["outro_sub"]),
                "URL": html.escape(host + T.get("rota", "")),
                "IMGS": imgs, "FIELDS": "\n          ".join(self.html_fields), "OVERLAYS": "\n        ".join(self.html),
                "AUDIO": "\n      ".join(self.audio), "ACTIONS": "\n      ".join(self.js), "OVERRIDES": "".join("\n" + o for o in overrides),
                "LANG": html.escape(lang), "MARCA": html.escape(T.get("marca") or self.prod["marca"]), "PRIMARY": primary,
                "PRIMARY_32": hex_rgba(primary, 0.32), "ACCENT_16": hex_rgba(accent, 0.16),
                "PRONTO": html.escape(T.get("pronto") or PRONTO.get(lang[:2].lower(), PRONTO["pt"]))}
        out = re.sub(r"\{\{([A-Z_0-9]+)\}\}", lambda m: vals[m.group(1)], tpl)
        (comp / "index.html").write_text(out, encoding="utf-8")
        nar = self.proj / "audio" / "narration.wav"
        if nar.exists():
            (comp / "assets").mkdir(parents=True, exist_ok=True)
            shutil.copy2(nar, comp / "assets" / "narration.wav")


# ---------------------------------------------------------------- prepare (fase A)

def prepare(proj: Path, cfg: dict, sfx_fn) -> str:
    """spec.json → evidências na composição, roteiro, step-map, storyboard provisório, brief e esqueleto."""
    f = proj / "spec.json"
    if not f.exists():
        raise ComposeError(f"{f} não existe")
    T = load(f)
    prod = product_info(proj)
    url = (T.get("url") or prod["url"]).rstrip("/")
    comp = proj / "composition"
    (comp / "assets").mkdir(parents=True, exist_ok=True)
    for k, name in T["imgs"].items():
        src = proj / "evidence" / name
        if not src.exists():
            raise ComposeError(f"imagem '{k}' não encontrada em evidence/: {name}")
        dst = comp / "assets" / name
        if not dst.exists() or dst.read_bytes() != src.read_bytes():
            shutil.copy2(src, dst)
    for fn in ("hyperframes.json", "package.json"):
        if not (comp / fn).exists():
            shutil.copy2(TPL / fn, comp / fn)
    (comp / "meta.json").write_text(json.dumps({"id": "composition", "name": proj.name}, indent=2), encoding="utf-8")
    brand = prod["brand_dir"]
    if brand and not (comp / "brand" / "brand.css").exists():
        shutil.copytree(brand, comp / "brand", dirs_exist_ok=True)
    if not (comp / "brand" / "brand.css").exists():
        raise ComposeError("sem marca: rode tutorial.py design-tokens (cria <produto>/02-marca/brand/) ou copie brand/ para composition/")
    if not (comp / "brand" / "logo.png").exists():
        raise ComposeError(f"a marca não tem logo.png ({comp / 'brand'}): a abertura e o fecho usam o logo")
    if not all((comp / "assets" / f"{w}.wav").exists() for w in ("click", "pop", "whoosh")):
        sfx_fn(comp / "assets")

    voice = cfg.get("voice", {})
    lang = cfg.get("language", "pt-BR")
    lines = [f"# Roteiro — {T['titulo']}", "", f"Direção: {voice.get('direction') or 'caloroso, confiante, ritmo médio, pausa curta entre frases.'}", ""]
    for sc in T["scenes"]:
        st = f"  [steps: {', '.join(sc['steps'])}]" if sc.get("steps") else ""
        lines += [f"## {sc['id']} — {sc.get('title', sc['id'])}{st}", sc["narration"], ""]
    (proj / "script.md").write_text("\n".join(lines), encoding="utf-8")

    H = {}
    if (proj / "evidence" / "boxes.json").exists():
        H.update(load(proj / "evidence" / "boxes.json"))
    H.update(T.get("caixas") or {})
    w0 = img_size(proj / "evidence" / T["imgs"][T["first_img"]])
    steps = []
    for s in T["steps"]:
        b = s["box"]
        if isinstance(b, str) and b not in H:
            raise ComposeError(f"passo {s['id']}: caixa '{b}' desconhecida")
        for k in ("img", "img_before"):
            if s.get(k) and s[k] not in T["imgs"]:
                raise ComposeError(f"passo {s['id']}: {k} '{s[k]}' não está em imgs ({', '.join(T['imgs'])})")
        d = {"id": s["id"], "title": s["title"], "user_action": s["user_action"], "result": s["result"], "screen": s["screen"]}
        if s.get("img_before"):
            d["evidence_before"] = f"evidence/{T['imgs'][s['img_before']]}"
        d.update({"evidence": f"evidence/{T['imgs'][s['img']]}", "box_source": "capture",
                  "target_box": list(H[b]) if isinstance(b, str) else list(b),
                  "capture_resolution": [w0[0], round(w0[0] * 9 / 16)], "ui_text": s.get("ui_text", []),
                  "sensitive": s.get("sensitive", []), "excluded": False, "notes": s.get("notes", "")})
        steps.append(d)
    sm = {"target": {"type": "APP WEB", "route": "W1", "locator": url + T.get("rota", ""),
                     "authorization": T.get("auth", ""), "capture_resolution": [w0[0], round(w0[0] * 9 / 16)]},
          "steps": steps}
    (proj / "step-map.json").write_text(json.dumps(sm, ensure_ascii=False, indent=1), encoding="utf-8")

    scenes, t = [], 0.0
    for sc in T["scenes"]:
        n = len(sc["narration"].replace("|", " ").split())
        dur = max(2.0, n / WPS + 1.0)
        extra = sc.get("extra", 0.6 if sc["layout"] == "title" else 1.0 if sc["layout"] == "outro" else 0.5)
        scenes.append({"id": sc["id"], "start": round(t, 3), "end": round(t + dur, 3), "layout": sc["layout"],
                       "steps": sc.get("steps", []), "extra": extra, "narration": sc["narration"], "audio": f"audio/{sc['id']}.wav",
                       "visual": sc.get("visual", ""), "camera": sc.get("camera", ""), "on_screen_text": sc.get("on_screen_text", []),
                       "transition_out": "fim" if sc["layout"] == "outro" else "corte contínuo"})
        t += dur
    sb = {"meta": {"title": T["titulo"], "slug": proj.name.split("-", 1)[-1] if re.match(r"^\d+-", proj.name) else proj.name,
                   "width": 1920, "height": 1080, "fps": cfg.get("fps", 30), "duration": round(t, 3), "language": lang,
                   "style": cfg.get("style", "clean-product"), "voice": voice.get("voice") or "", "wps": WPS,
                   "screen_box": [WX, WY + BAR, VW, VH]}, "scenes": scenes}
    if T.get("slug"):
        sb["meta"]["slug"] = T["slug"]
    (proj / "storyboard.json").write_text(json.dumps(sb, ensure_ascii=False, indent=2), encoding="utf-8")

    (proj / "brief.md").write_text(
        f"# Brief — {T['titulo']}\n\n- Produto: {prod['nome'] or url} ({url}{T.get('rota', '')})"
        + (f", perfil {T['perfil']}" if T.get("perfil") else "") + "\n"
        + (f"- Objetivo: {T['objetivo']}\n" if T.get("objetivo") else "")
        + (f"- Público: {T['publico']}\n" if T.get("publico") else "")
        + f"- Formato: {cfg.get('format', '16:9')} · voz {voice.get('engine', 'edge')}:{voice.get('voice') or 'padrão'}"
        + f" · legenda {cfg.get('captions', {}).get('style', 'highlight')}\n"
        + f"- Idiomas: {', '.join(cfg.get('idiomas') or ['pt-BR', 'en-US', 'es'])} (mesma imagem)\n"
        + "- Fonte: spec.json → tutorial.py prepare/compose (nada de HTML escrito à mão)\n", encoding="utf-8")
    return f"{len(T['imgs'])} evidências, {len(steps)} passos, {len(scenes)} cenas"
