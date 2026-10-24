"""Captura determinística do T2: um roteiro em JSON → screenshots de página inteira + caixas medidas no DOM.

O agente declara o que fotografar e quais elementos medir; o script entra pelo atalho de teste (nenhuma senha),
troca dados pessoais por fictícios no DOM local antes de cada foto e grava, em pixels da captura:
  <saida>/<nome>.png     página inteira (viewport × escala)
  <saida>/boxes.json     {"<nome>:<elemento>": [x, y, w, h]}   → spec.json referencia por nome (tutorial.py compose)
  <saida>/textos.json    {"<nome>:<elemento>": "texto visível"}  → ui_text dos passos

Duas travas, ambas antes de qualquer foto ou clique:
  1. Privacidade: cada regra de troca é validada no navegador; a troca roda de novo logo antes de medir e de
     fotografar (campos preenchidos por JavaScript não disparam mutação); e, se algum valor real de "ficticios" ou
     algum padrão de "ficticios_rx" ainda aparecer no texto ou nos campos da página, a captura PARA sem gravar a foto.
  2. Só observação: um clique só acontece sem autorização se o elemento REAL encontrado (texto, aria-label, title,
     <title> de ícone) for claramente de navegação — aba, filtro, visualização, ordenação, paginação, ver detalhes,
     link interno. Qualquer outro (inclusive botão só com ícone) exige "autorizado": true no passo, e o agente só põe
     isso com a autorização do usuário para aquela ação. "selecionar" só sem autorização em filtro; "ir" recusa rotas
     com cara de ação. Nasceu de cadastros-conexao/04-geradores/equipe/capture.py e de um incidente real: o nome
     parcial "Lista" casou com "Inativar Analista…" e inativou uma conta.

Roteiro (references/02-captura-por-alvo.md §W1):
  {"base": "https://app.exemplo.com", "entrar": {"clicar": LOC} | null, "viewport": [1280, 720], "escala": 1.5,
   "ficticios": {"Nome Real": "Nome Fictício"}, "ficticios_rx": [["\\\\d{3}\\\\.\\\\d{3}", "000.000"]],
   "passos": [{"ir": "/rota"}, {"clicar": LOC}, {"selecionar": LOC, "opcao": "Todos"}, {"digitar": LOC, "texto": "abc"},
              {"rolar": 600}, {"esperar": 1500}, {"capturar": "home", "caixas": {"busca": LOC}}]}
  LOC = {"papel": "button", "nome": "Exportar CSV", "exato": true} | {"texto": "Exibindo"} | {"css": "table"}
        + opcionais "n": 2 (n-ésimo), "ultimo": true, "subir": 1 (níveis acima) | "cartao" (sobe até o cartão)
"""
from __future__ import annotations

import json
import re
from pathlib import Path

# o que é inequivocamente escrita (vale mesmo se também parecer navegação)
ACAO_PERIGOSA = re.compile(
    r"\b(salvar|gravar|enviar|reenviar|excluir|exclua|apagar|remover|deletar|inativar|desativar|ativar|reativar|"
    r"bloquear|desbloquear|arquivar|desarquivar|gerar|criar|cadastrar|adicionar|incluir|nov[oa]|duplicar|importar|"
    r"exportar|imprimir|baixar|download|publicar|aprovar|reprovar|rejeitar|confirmar|concluir|finalizar|cancelar|"
    r"atualizar|alterar|editar|mover|transferir|convidar|resetar|redefinir|restaurar|pagar|comprar|assinar|sair|logout|"
    r"sim|ok|save|submit|send|delete|remove|create|add|new|update|edit|confirm|approve|reject|cancel|archive|invite|"
    r"publish|pay|buy|sign ?out|log ?out|yes)\b", re.I)
# o que é claramente navegação/observação
NAVEGACAO = re.compile(
    r"^(visualiza[çc][ãa]o( em)?\b|ver\b|visualizar\b|mostrar\b|exibir\b|abrir detalhes|detalhes\b|fila\b|"
    r"relat[óo]rios\b|m[ée]tricas\b|hoje$|ontem$|\d+\s?d(ias)?$|recentes$|a-z$|z-a$|todos\b|todas\b|ativos$|inativos$|"
    r"cards$|lista$|kanban$|mapa$|tabela$|grade$|anterior$|pr[óo]xim[oa]$|limpar (filtros|todos)$|fechar$|voltar$|"
    r"expandir$|recolher$|filtr|orden|aba\b|painel\b|in[íi]cio$|vis[ãa]o geral)", re.I)
ROTA_PERIGOSA = re.compile(r"logout|sair|signout|sign-out|delete|excluir|remov|apagar|destroy|reset|enviar|submit|send|"
                           r"aprovar|approve|reject|rejeitar|cancel|export|download|token|/api/", re.I)
FILTRO = re.compile(r"status|situa[çc][ãa]o|filtr|orden|per[íi]odo|departamento|tipo|colaborador|categoria|exibir|"
                    r"mostrar|itens por p[áa]gina|por p[áa]gina|visualiza", re.I)

TROCA_JS = """
(() => {
  const M = window.__ficticios || {};
  const RX = (window.__ficticiosRx || []).map(([re, b]) => { try { return [new RegExp(re, 'g'), b]; }
    catch (e) { window.__ficticiosErro = String(re) + ': ' + e.message; return null; } }).filter(Boolean);
  const fix = (s) => { if (!s) return s; let o = s; for (const [a, b] of Object.entries(M)) o = o.split(a).join(b);
    for (const [re, b] of RX) o = o.replace(re, b); return o; };
  const walk = (root) => {
    const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let n; while ((n = w.nextNode())) { const v = fix(n.nodeValue); if (v !== n.nodeValue) n.nodeValue = v; }
    root.querySelectorAll && root.querySelectorAll('input,textarea').forEach(e => { const v = fix(e.value); if (v !== e.value) e.value = v;
      const p = fix(e.placeholder); if (p !== e.placeholder) e.placeholder = p; });
    root.querySelectorAll && root.querySelectorAll('[title],[aria-label],[alt]').forEach(e => {
      for (const at of ['title', 'aria-label', 'alt']) { const o = e.getAttribute(at); if (o) { const v = fix(o); if (v !== o) e.setAttribute(at, v); } } });
  };
  // vazamento: algum valor real ou padrão ainda visível no texto ou nos campos?
  window.__vazamento = () => { const txt = document.body.innerText + '\\n' +
      [...document.querySelectorAll('input,textarea')].map(e => e.value).join('\\n');
    const fict = Object.values(M).join('\\n');
    for (const a of Object.keys(M)) if (a && !fict.includes(a) && txt.includes(a)) return a;
    // o fictício pode casar com o próprio padrão (CPF 000.000.000-00): só vaza o que não é o valor de troca
    for (const [re, b] of RX) { re.lastIndex = 0; let m; while ((m = re.exec(txt))) { if (m[0] !== b) return m[0];
      if (m.index === re.lastIndex) re.lastIndex++; } }
    return null; };
  window.__trocar = () => document.body && walk(document.body);
  const go = () => { walk(document.body); new MutationObserver(ms => ms.forEach(m => {
      if (m.type === 'characterData') { const v = fix(m.target.nodeValue); if (v !== m.target.nodeValue) m.target.nodeValue = v; }
      m.addedNodes.forEach(x => x.nodeType === 3 ? (x.nodeValue = fix(x.nodeValue)) : x.nodeType === 1 && walk(x)); }))
    .observe(document.body, { childList: true, subtree: true, characterData: true }); };
  document.body ? go() : document.addEventListener('DOMContentLoaded', go);
})();
"""

MEDE_JS = """(e, up) => {
  if (up === 'cartao') { while (e.parentElement && e.parentElement.getBoundingClientRect().width < e.getBoundingClientRect().width * 1.4) e = e.parentElement; }
  else for (let i = 0; i < (up || 0); i++) e = e.parentElement;
  const r = e.getBoundingClientRect();
  return [r.x + scrollX, r.y + scrollY, r.width, r.height, (e.innerText || e.value || '').trim().replace(/\\s+/g, ' ').slice(0, 160)]; }"""

# tudo o que identifica o elemento de verdade: texto, rótulos, ícone (<title> do svg), destino do link e papel
REAL_JS = """e => ({ rotulos: [e.innerText, e.value, e.getAttribute('aria-label'), e.title, e.getAttribute('alt'),
    ...[...e.querySelectorAll('svg title, img[alt]')].map(x => x.textContent || x.getAttribute('alt'))]
    .filter(Boolean).map(x => x.replace(/\\s+/g, ' ').trim().slice(0, 120)).filter(Boolean),
  href: e.getAttribute('href') || '', papel: e.getAttribute('role') || e.tagName.toLowerCase(),
  selecionado: e.getAttribute('aria-selected') })"""


class CaptureError(Exception):
    pass


def locator(pg, loc: dict):
    if "papel" in loc:
        kw = {"exact": loc.get("exato", True)}
        if "nome" in loc:
            kw["name"] = loc["nome"]
        if "nivel" in loc:
            kw["level"] = loc["nivel"]
        L = pg.get_by_role(loc["papel"], **kw)
    elif "texto" in loc:
        L = pg.get_by_text(loc["texto"], exact=loc.get("exato", False))
    elif "css" in loc:
        L = pg.locator(loc["css"])
    else:
        raise CaptureError(f"localizador sem papel/texto/css: {loc}")
    if loc.get("ultimo"):
        return L.last
    return L.nth(loc["n"]) if "n" in loc else L.first


def descrever(loc: dict) -> str:
    return loc.get("nome") or loc.get("texto") or loc.get("css") or loc.get("papel", "?")


def clique_seguro(real: dict) -> tuple[bool, str]:
    """(pode clicar sem autorização?, motivo). Cada rótulo do elemento (texto, aria-label, title, ícone) é avaliado:
    algum de escrita → não; algum de navegação → sim; sem rótulo (só ícone sem título) → não."""
    rotulos = real.get("rotulos")
    if rotulos is None:
        rotulos = [real["texto"]] if real.get("texto") else []
    t = " / ".join(rotulos)
    if not rotulos:
        return False, "elemento sem texto nem rótulo (botão só com ícone)"
    if any(ACAO_PERIGOSA.search(r) for r in rotulos):
        return False, f"'{t}' parece ação de escrita"
    if real.get("href") and ROTA_PERIGOSA.search(real["href"]):
        return False, f"link para '{real['href']}' parece ação"
    if real.get("papel") in ("tab", "option", "menuitemradio") or any(NAVEGACAO.search(r) for r in rotulos):
        return True, ""
    if real.get("papel") == "a" and real.get("href", "").startswith(("/", "#", "?")):
        return True, ""
    return False, f"'{t}' não é navegação reconhecida (aba, filtro, visualização, ordenação, paginação, detalhes)"


def checar_roteiro(roteiro: dict) -> None:
    """O que dá para recusar sem abrir o navegador: nomes pedidos com cara de escrita, rotas com cara de ação."""
    for i, p in enumerate(roteiro.get("passos", []), 1):
        if p.get("autorizado"):
            continue
        if "clicar" in p and ACAO_PERIGOSA.search(descrever(p["clicar"])):
            raise CaptureError(f"passo {i}: clicar em '{descrever(p['clicar'])}' parece ação que grava dados; "
                               "só com 'autorizado': true, depois de o usuário autorizar")
        if "ir" in p and ROTA_PERIGOSA.search(p["ir"]):
            raise CaptureError(f"passo {i}: ir para '{p['ir']}' parece ação (sair, excluir, exportar…); só com 'autorizado': true")
        nome_sel = descrever(p["selecionar"]) if "selecionar" in p else ""
        # select com número no nome ("Situação do cliente 9") é de um registro, não filtro da lista
        if "selecionar" in p and (re.search(r"\d", nome_sel) or not (
                FILTRO.search(nome_sel + " " + str(p.get("opcao", "")))
                or str(p.get("opcao", "")).lower().startswith(("todos", "todas")))):
            raise CaptureError(f"passo {i}: selecionar em '{descrever(p['selecionar'])}' não parece filtro (um select pode "
                               "gravar ao mudar); só com 'autorizado': true")


def capture(roteiro: dict, saida: Path, chrome: str | None, log=print) -> dict:
    checar_roteiro(roteiro)
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise CaptureError("playwright para Python ausente (pip install playwright: peça OK ao usuário)") from None
    vw, vh = roteiro.get("viewport", [1280, 720])
    escala = float(roteiro.get("escala", 1.5))
    base = roteiro["base"].rstrip("/")
    saida.mkdir(parents=True, exist_ok=True)
    boxes_f, textos_f = saida / "boxes.json", saida / "textos.json"
    boxes = json.loads(boxes_f.read_text(encoding="utf-8")) if boxes_f.exists() else {}
    textos = json.loads(textos_f.read_text(encoding="utf-8")) if textos_f.exists() else {}
    fotos, faltas = [], []
    pw = sync_playwright().start()
    try:
        b = pw.chromium.launch(**({"executable_path": chrome} if chrome else {}))
        pg = b.new_page(viewport={"width": vw, "height": vh}, device_scale_factor=escala,
                        locale=roteiro.get("idioma", "pt-BR"), timezone_id=roteiro.get("fuso", "America/Sao_Paulo"),
                        reduced_motion="reduce")
        pg.add_init_script(f"window.__ficticios = {json.dumps(roteiro.get('ficticios') or {}, ensure_ascii=False)}; "
                           f"window.__ficticiosRx = {json.dumps(roteiro.get('ficticios_rx') or [], ensure_ascii=False)};"
                           + TROCA_JS)
        pg.set_default_timeout(int(roteiro.get("timeout_ms", 3000)))
        pg.set_default_navigation_timeout(30000)
        pg.goto(base)
        pg.wait_for_timeout(1500)
        erro_rx = pg.evaluate("window.__ficticiosErro || null")
        if erro_rx:   # regra inválida em JavaScript (ex.: sintaxe só do Python): sem troca, sem captura
            raise CaptureError(f"ficticios_rx inválida no navegador: {erro_rx}")
        if roteiro.get("entrar"):
            locator(pg, roteiro["entrar"]["clicar"]).click()   # atalho de teste da tela de login: nenhuma senha
            pg.wait_for_timeout(int(roteiro["entrar"].get("esperar", 4000)))
        for i, p in enumerate(roteiro.get("passos", []), 1):
            espera = int(p.get("esperar_depois", 1200))
            if "ir" in p:
                pg.goto(p["ir"] if p["ir"].startswith("http") else base + p["ir"])
                pg.wait_for_timeout(int(p.get("esperar_depois", 3000)))
            elif "clicar" in p:
                alvo = locator(pg, p["clicar"])
                # o nome pedido pode casar com outro elemento ("Lista" dentro de "Inativar Analista…"):
                # confere o que o elemento encontrado É antes de clicar
                real = alvo.evaluate(REAL_JS)
                ok, motivo = clique_seguro(real)
                if not ok and not p.get("autorizado"):
                    raise CaptureError(f"passo {i}: o elemento encontrado para '{descrever(p['clicar'])}' não foi clicado: "
                                       f"{motivo}. Se for mesmo o que o usuário autorizou, marque 'autorizado': true")
                alvo.click()
                pg.wait_for_timeout(espera)
            elif "selecionar" in p:
                alvo = locator(pg, p["selecionar"])
                # dentro de linha de tabela, cartão ou formulário o select costuma gravar ao mudar
                dentro = alvo.evaluate("e => !!e.closest('tr,[role=row],article,li,form,[role=dialog]')")
                if dentro and not p.get("autorizado"):
                    raise CaptureError(f"passo {i}: o select '{descrever(p['selecionar'])}' está dentro de linha, cartão "
                                       "ou formulário (pode gravar ao mudar); só com 'autorizado': true")
                alvo.select_option(label=p["opcao"])
                pg.wait_for_timeout(espera)
            elif "digitar" in p:
                locator(pg, p["digitar"]).fill(p["texto"])   # sem Enter: nada é enviado
                pg.wait_for_timeout(espera)
            elif "rolar" in p:
                pg.evaluate(f"window.scrollTo(0, {int(p['rolar'])})")
                pg.wait_for_timeout(400)
            elif "esperar" in p:
                pg.wait_for_timeout(int(p["esperar"]))
            elif "capturar" in p:
                nome = p["capturar"]
                pg.evaluate("window.scrollTo(0, 0)")
                pg.wait_for_timeout(400)
                pg.evaluate("window.__trocar()")   # campos preenchidos por JS (React/Vue) não disparam mutação
                vaz = pg.evaluate("window.__vazamento()")
                if vaz:
                    raise CaptureError(f"captura '{nome}' interrompida: dado real ainda visível na página ({vaz[:3]}…); "
                                       "inclua-o em 'ficticios' ou ajuste 'ficticios_rx'. Nada foi fotografado")
                for k, loc in (p.get("caixas") or {}).items():
                    try:
                        r = locator(pg, loc).evaluate(MEDE_JS, loc.get("subir", 0))
                    except Exception as ex:
                        faltas.append(f"{nome}:{k}")
                        log(f"  sem caixa {nome}:{k} ({str(ex).splitlines()[0][:80]})")
                        continue
                    boxes[f"{nome}:{k}"] = [round(v * escala) for v in r[:4]]
                    if r[4]:
                        textos[f"{nome}:{k}"] = r[4]
                pg.evaluate("window.__trocar()")
                if pg.evaluate("window.__vazamento()"):
                    raise CaptureError(f"captura '{nome}' interrompida: dado real reapareceu antes da foto")
                pg.screenshot(path=str(saida / f"{nome}.png"), full_page=True)
                fotos.append(nome)
                log(f"ok {nome}.png ({len(p.get('caixas') or {})} caixas)")
            else:
                raise CaptureError(f"passo {i} sem verbo conhecido: {p}")
        b.close()
    finally:
        pw.stop()
        boxes_f.write_text(json.dumps(boxes, ensure_ascii=False, indent=1), encoding="utf-8")
        textos_f.write_text(json.dumps(textos, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"fotos": fotos, "caixas": len(boxes), "faltas": faltas}
