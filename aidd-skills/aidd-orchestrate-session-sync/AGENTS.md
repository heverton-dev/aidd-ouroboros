# Diretrizes para Agentes — aidd-orchestrate-session-sync

Quando o usuario pedir para salvar a sessao, fazer pausa, registrar o historico ou exportar os prompts/respostas:
1. Dispare `python aidd-skills/aidd-orchestrate-session-sync/scripts/session_sync.py`.
2. Verifique a criacao/atualizacao do arquivo em `secoes/sessao_<id>_dialogos_completos.json`.
3. Retorne link direto para o arquivo gerado sem reproduzir o texto integral na resposta.
