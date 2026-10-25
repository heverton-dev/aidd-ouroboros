# Session Sync Specification

## 1. Protocolo de Sincronização Universal
O sincronizador de sessão consolida o histórico factual de turnos entre o usuário e o modelo em formato estruturado.

## 2. Estrutura do Envelope
- `session_id`: Identificador determinístico da sessão.
- `turn_index`: Índice sequencial do turno.
- `source`: Origem (`user` ou `model`).
- `timestamp`: Marca temporal ISO 8601 UTC.
- `content_pointer`: Ponteiro de integridade com digest SHA-256 para payloads volumosos.
