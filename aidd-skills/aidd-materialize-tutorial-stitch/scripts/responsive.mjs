// Medidor de responsividade da aidd-tutorial-creator (somente leitura).
// Para cada viewport: abre a URL (opcionalmente entra por um atalho de teste), mede meta viewport, rolagem
// horizontal, elementos vazando da tela e o menor texto visível, e salva um screenshot.
// Uso: node responsive.mjs <config.json>   (o tutorial.py monta o config e localiza o playwright-core)
import { createRequire } from "node:module";
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { join } from "node:path";

const cfg = JSON.parse(readFileSync(process.argv[2], "utf8"));
const require = createRequire(cfg.playwright_from);
const { chromium } = require("playwright-core");

const measure = () => {
  const vw = window.innerWidth;
  const meta = document.querySelector('meta[name="viewport"]')?.getAttribute("content") || null;
  const sw = Math.max(document.documentElement.scrollWidth, document.body ? document.body.scrollWidth : 0);
  // elementos dentro de contêiner com rolagem/corte horizontal próprio (carrossel, tabela) não quebram a página:
  // contam como "clipped" (conteúdo cortado dentro do contêiner), não como vazamento da página
  const inScroller = (el) => {
    for (let p = el.parentElement; p && p !== document.body; p = p.parentElement) {
      const ox = getComputedStyle(p).overflowX;
      if (ox === "auto" || ox === "scroll" || ox === "hidden" || ox === "clip") return true;
    }
    return false;
  };
  let overflow = 0, clipped = 0, texts = 0, tiny = 0, minFont = 999;
  const walker = document.createTreeWalker(document.body || document.documentElement, NodeFilter.SHOW_ELEMENT);
  for (let el = walker.currentNode; el; el = walker.nextNode()) {
    const st = getComputedStyle(el);
    if (st.display === "none" || st.visibility === "hidden" || Number(st.opacity) === 0) continue;
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    if (r.right > vw + 2 && st.position !== "fixed") { if (inScroller(el)) clipped++; else overflow++; }
    const ownText = [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim().length > 1);
    if (ownText && r.top < window.innerHeight * 3) {
      const fs = parseFloat(st.fontSize);
      texts++;
      if (fs < 10) tiny++;
      if (fs < minFont) minFont = fs;
    }
  }
  return { viewport_width: vw, meta_viewport: meta, scroll_width: sw, horizontal_scroll: sw > vw + 2,
           overflowing_elements: overflow, clipped_in_scrollers: clipped, text_elements: texts, tiny_text_share: texts ? +(tiny / texts).toFixed(3) : 0,
           min_font_px: minFont === 999 ? null : minFont };
};

const browser = await chromium.launch({ executablePath: cfg.chrome, headless: true });
const results = [];
mkdirSync(cfg.out, { recursive: true });
for (const vp of cfg.viewports) {
  const ctx = await browser.newContext({ viewport: { width: vp.width, height: vp.height }, deviceScaleFactor: vp.dsf,
                                         isMobile: !!vp.mobile, hasTouch: !!vp.mobile, locale: cfg.locale || "pt-BR" });
  const page = await ctx.newPage();
  const pages = [];
  try {
    await page.goto(cfg.url, { waitUntil: "load", timeout: 45000 });
    await page.waitForTimeout(1500);
    if (cfg.login) {
      await page.getByRole(cfg.login.role || "button", { name: cfg.login.name, exact: true }).click({ timeout: 15000 });
      await page.waitForTimeout(cfg.login.wait_ms || 4000);
    }
    const paths = cfg.paths && cfg.paths.length ? cfg.paths : [null];
    for (const p of paths) {
      if (p) { await page.goto(new URL(p, cfg.url).href, { waitUntil: "load", timeout: 45000 }); await page.waitForTimeout(2000); }
      const m = await page.evaluate(measure);
      const shot = join(cfg.out, `${vp.formato.replace(":", "x")}-${(p || "inicio").replace(/[^a-z0-9]+/gi, "_")}.png`);
      await page.screenshot({ path: shot });
      // calibrado olhando screenshots reais: rótulos de 10 px em caixa alta são normais em mobile;
      // carrossel/tabela com rolagem própria não quebra a página, mas muito conteúdo cortado = "parcial"
      const base = !!(m.meta_viewport && /width\s*=\s*device-width/i.test(m.meta_viewport)) && !m.horizontal_scroll
                   && m.overflowing_elements <= 2 && (m.min_font_px ?? 99) >= 9 && m.tiny_text_share <= 0.1;
      const nivel = !base ? "nao" : m.clipped_in_scrollers > 40 ? "parcial" : "sim";
      pages.push({ caminho: p || page.url().replace(/^https?:\/\/[^/]+/, ""), ...m, nivel, responsivo: nivel !== "nao",
                   screenshot: shot });
    }
  } catch (e) {
    pages.push({ erro: String(e).slice(0, 300), responsivo: false });
  }
  await ctx.close();
  const niveis = pages.map((x) => x.nivel || "nao");
  results.push({ formato: vp.formato, viewport: `${vp.width}x${vp.height}@${vp.dsf}`, mobile: !!vp.mobile,
                 nivel: niveis.includes("nao") ? "nao" : niveis.includes("parcial") ? "parcial" : "sim",
                 responsivo: pages.length > 0 && pages.every((x) => x.responsivo), paginas: pages });
}
await browser.close();
writeFileSync(join(cfg.out, "responsive.json"), JSON.stringify({ url: cfg.url, resultados: results }, null, 2));
console.log(JSON.stringify(results.map((r) => ({ formato: r.formato, viewport: r.viewport, responsivo: r.responsivo }))));
