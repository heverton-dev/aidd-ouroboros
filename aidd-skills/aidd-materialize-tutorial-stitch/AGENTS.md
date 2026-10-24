# AGENTS.md — Contrato de Governança para Agentes (aidd-materialize-tutorial-stitch)

Diretrizes para agentes de IA operando a skill `aidd-materialize-tutorial-stitch`.
Padrão: AIDD Universal Architecture / Zero Stubs / Token Economy (< 300t).

1. **Eficiência de Contexto (Lazy Loading):** Leia apenas as referências da etapa atual em `references/`. Nunca carregue todo o diretório na memória.
2. **Determinismo:** Utilize sempre os scripts locais em `scripts/` para compilar e alinhar tutoriais animados.
3. **Padrão de Handoff por Ponteiros:** Toda saída deve ser serializada em JSON apontando os arquivos de vídeo/imagem com seus hashes SHA-256 via `motores/governanca/handoff_crypto.py`.
4. **Gates:** Validação de AST obrigatória (`python -m motores.governanca.gate_ast`).
