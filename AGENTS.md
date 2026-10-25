# AIDD Ouroboros Governance & Agent Directives

> **Projeto:** `aidd-ouroboros` | **Padrão:** Zero Stubs, Strict Determinism, Token Economy (< 500t), Pointer Architecture.
> **Universal Quality Gate:** `python motores/governanca/audit_runner.py` (deve retornar exit 0).

---

## 1. Regras Invioláveis de Execução (Core Laws)

1. **Determinism First:** Use scripts em `motores/`, `scripts/` ou ferramentas AST antes de raciocinar com o LLM para tarefas mecânicas (geração de ID, hash, schemas, validações).
2. **Economia Extrema de Tokens (Pointer Architecture):**
   - **NÃO** despeje arquivos inteiros, vídeos ou dados massivos nos prompts ou respostas.
   - Utilize a passagem por ponteiros locais (`manifest.json` com `path` e `sha256`) gerados via `motores/governanca/handoff_crypto.py`.
   - Limite respostas a dados objetivos, tabelas concisas e links `file://`.
3. **Zero Stubs / Zero Mocks:** Código em Python deve ser completo, tipado e funcional. O uso de `pass`, `TODO`, `...` ou `NotImplementedError` em funções de negócio é bloqueado pelo `gate_ast.py`.
4. **Handoffs Criptográficos Imutáveis:** Toda passagem de bastão entre skills de pipeline ou agentes deve ser assinada via HMAC-SHA256 e conter verificação de integridade no disco.
5. **Micro-Frontmatter Obrigatório:** O campo `description:` em qualquer `SKILL.md` gerado deve conter no máximo 25 palavras.
6. **Governança Fractal:** Toda nova skill (`aidd-orchestrate-skill-creator`) ou pipeline (`aidd-orchestrate-pipeline-creator`) gerado deve herdar seu próprio `AGENTS.md` compacto (< 400 palavras) e testes de gate correspondentes.
7. **Proibição de Criação Ad-Hoc (Flywheel Soberano):** É estritamente proibido criar ou editar skills ou pipelines de forma artesanal/ad-hoc via LLM. Toda nova skill ou pipeline deve ser provisionada exclusivamente através dos criadores canônicos (`pipeline_creator.py` e `skill_creator.py`) com anatomia enterprise completa (`references/`, `templates/`, `scripts/`, `dependencies.json`, `RULES.md`, `sync.ps1`).

---

## 2. Comandos Canônicos do Ouroboros

```bash
# Executar todos os Quality Gates (incluindo Circuit Breaker)
python ouroboros.py --audit

# Diagnóstico de pré-voo e credenciais
python ouroboros.py --doctor

# Setup e sincronização multi-harness
powershell -File setup.ps1

# Disparar pipeline específico
python ouroboros.py --pipeline canal-dark-avatar
```
