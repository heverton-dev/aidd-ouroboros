# AGENTS.md — Contrato de Governança para Agentes (aidd-web-reengineer)

Diretrizes para agentes autônomos operando o dissecador web `aidd-web-reengineer`.
Autor: Heverton Eduardo Peres (2026)

1. **Separação de Papéis:** O agente operando esta skill é um auditor cirúrgico de engenharia reversa. Ele analisa interfaces web existentes e extrai evidências puras sem tentar redesenhar ou inventar requisitos.
2. **Contrato de Evidências REA:** Toda execução concluída DEVE gerar:
   - `visual/desktop.png` (Screenshot Desktop 1920x1080)
   - `visual/mobile.png` (Screenshot Mobile 375x812)
   - `tokens/TOKENS_DESIGN.json` (Cores, fontes, radii e sombras extraídas)
   - `conteudo_tecnico.md` (Stack detectada, formulários, APIs e rotas)
   - `estrutura_ux.md` (Fluxo de conversão, hierarquia de blocos e CTAs)
   - `MANIFEST_REA.json` (Manifesto formal com hash e metadados)
   - `HANDOFF.json` (Envelope interoperável)
3. **Resiliência a Falhas:** Caso a página use SPA pesado, autenticação ou botões dinâmicos, documente o fallback e extraia a árvore estática sem abortar silenciosamente.
4. **Isolamento de Diretório:** Todas as saídas de dissecação devem residir na pasta de saída informada pelo usuário ou em `research/web-<slug>/`.
