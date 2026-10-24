# AGENTS.md — Contrato de Governança para Agentes (aidd-social-reengineer)

Diretrizes para agentes autônomos operando o dissecador social `aidd-social-reengineer`.
Autor: Heverton Eduardo Peres (2026)

1. **Separação de Papéis:** O agente operando esta skill disseca carrosséis e posts estáticos em seus componentes fundamentais: copywriting, ganchos visuais e design tokens. Ele não reescreve nem cria novos posts, apenas extrai com exatidão matemática o que funciona no conteúdo original.
2. **Contrato de Evidências REA:** Toda dissecação concluída DEVE emitir:
   - `visual/slides/` (Imagens individuais dos slides numerados)
   - `tokens/TOKENS_DESIGN.json` (Paleta de cores e tipografia dominante)
   - `conteudo_tecnico.md` (Texto transcrito slide a slide com metadados)
   - `estrutura_narrativa.md` (Dissecação do Hook, Retenção e CTA)
   - `MANIFEST_REA.json` (Manifesto formal com hash e metadados)
   - `HANDOFF.json` (Envelope universal de entrega)
3. **Respeito à Sequência:** A ordem cronológica dos slides (1 a N) deve ser mantida estritamente para não quebrar a lógica narrativa.
4. **Isolamento de Diretório:** Todas as evidências devem residir na pasta de saída informada pelo usuário.
