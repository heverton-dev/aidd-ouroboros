# AGENTS.md — Contrato de Governança para Agentes (aidd-app-reengineer)

Diretrizes para agentes autônomos operando o dissecador de apps `aidd-app-reengineer`.
Autor: Heverton Eduardo Peres (2026)

1. **Separação de Papéis:** O agente operando esta skill atua como um engenheiro reverso forense. Sua responsabilidade é desempacotar, extrair e catalogar componentes de APKs e binários sem alterar o código original.
2. **Contrato de Evidências REA:** Toda dissecação concluída DEVE emitir:
   - `tokens/TOKENS_DESIGN.json` (Paleta de cores e temas extraídos do app)
   - `conteudo_tecnico.md` (Package, permissões, activities, APIs e serviços)
   - `arquitetura.md` (Fluxo de telas e grafo de dependências)
   - `MANIFEST_REA.json` (Manifesto formal com hash e metadados)
   - `HANDOFF.json` (Envelope universal de entrega)
3. **Segurança e Isolamento:** Não execute código dinâmico não confiável. Realize apenas análise estática e extração de recursos em sandbox.
4. **Isolamento de Diretório:** Todo conteúdo extraído deve residir na pasta de saída especificada pelo usuário.
