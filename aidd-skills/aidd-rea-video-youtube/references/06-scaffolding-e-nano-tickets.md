# 06 — Scaffolding e Decomposição em Nano-Tickets

## 1. O Conceito de Nano-Tickets Tracer Bullet
Um nano-ticket tracer bullet atravessa verticalmente todas as camadas necessárias para entregar uma funcionalidade observável:
- **NUNCA** crie tickets de "apenas setup de types", "apenas escrever testes" ou "apenas criar pastas".
- Cada ticket deve conter seu teste, sua implementação e sua validação.

## 2. Invariantes de Decomposição
1. **Context Window Fit:** O ticket deve ser pequeno o suficiente para ser lido e executado por um agente a partir de um contexto zerado (fresh context), sem depender do histórico do chat.
2. **Critérios de Validação Binários:** O comando declarado em `Validation Command` deve obrigatoriamente falhar no código atual e passar após a implementação. Comandos como `echo ok` ou `exit 0` são sumariamente reprovados.
3. **DAG Explícito:** Todo ticket indica claramente `Blocked by: TK-XX` ou `Blocked by: none`, permitindo execução em paralelo ou sequencial sem ciclos.
