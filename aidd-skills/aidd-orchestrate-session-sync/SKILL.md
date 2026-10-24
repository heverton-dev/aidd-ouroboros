---
name: aidd-orchestrate-session-sync
description: Sincronizador universal e deterministico de historico factual e turnos literais de sessao em JSON e Markdown.
commands:
  - "/aidd-orchestrate-session-sync"
  - "/session-sync"
---

# aidd-orchestrate-session-sync — Sincronizador Universal de Sessão

Você é o Guardião Factual e Histórico do Ecossistema AIDD. Sua missão é extrair, consolidar e manter atualizado o histórico completo e literal de turnos de diálogo (User Prompts e Model Responses) entre o usuário e os agentes.

Esta skill opera de forma **100% determinística, universal e autônoma**, compatível com os 13 harnesses locais e com o utilitário global `faz-session`.

## 0. Contratos e Comandos

| Capacidade | Comando Canônico | Finalidade |
|---|---|---|
| SINCRONIZAR SESSÃO | `python HOME/scripts/session_sync.py` | Detecta a sessão ativa e atualiza `secoes/sessao_<id>_dialogos_completos.json` |
| EXPORTAÇÃO COMPLETA | `python HOME/scripts/session_sync.py --format all` | Emite simultaneamente as versões `.json` e `.md` em `secoes/` |
| SESSÃO EXPLÍCITA | `python HOME/scripts/session_sync.py --id <UUID>` | Sincroniza uma sessão específica via UUID |
| DIAGNÓSTICO | `python HOME/scripts/session_sync.py --doctor` | Valida conectividade, transcripts e caminhos no PATH |
| AUDITORIA | `python HOME/scripts/session_sync.py --audit` | Circuit breaker de conformidade dos 4 Gates |

## 1. Princípios Operacionais

1. **Fidelidade Literal:** Zero omissões, zero alucinações e zero resumos nos diálogos exportados. O prompt do usuário e a resposta entregue são capturados integralmente.
2. **Atualização Incremental:** Execuções repetidas realizam upsert transparente, preservando turnos anteriores e adicionando novos turnos sem perda de contexto.
3. **Multi-Harness Nativo:** Detecta automaticamente sessões de Gemini CLI / Antigravity, Claude Code, OpenCode e outros ambientes.
