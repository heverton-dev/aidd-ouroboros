# AGENTS.md — Contrato de Governança para Pipeline (video-to-tutorial)

Diretrizes para agentes de IA operando o pipeline `video-to-tutorial`.
Padrão: AIDD Universal Architecture / Zero Stubs / Token Economy (< 300t).

1. **Ordem Topológica Rígida:** Execute os nós através de `run_pipeline.py`. Não pule etapas do DAG.
2. **Passagem por Ponteiros (Pointer Architecture):** Os dados trocados entre nós usam o envelope criptográfico HMAC-SHA256 (`motores/governanca/handoff_crypto.py`). Nunca injete payloads inteiros no prompt.
3. **Zero Mocks:** Toda etapa deve invocar seu script operacional real ou falhar explicitamente.
4. **Gates:** Valide a integridade do estado e dos dados em disco antes de declarar conclusão.
