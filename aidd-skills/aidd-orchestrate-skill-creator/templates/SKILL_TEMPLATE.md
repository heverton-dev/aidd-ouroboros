---
name: {{SKILL_NAME}}
description: {{MICRO_DESCRIPTION}}
commands:
  - "/{{SKILL_NAME}}"
  - "/{{SHORT_NAME}}"
---

# {{UPPERCASE_NAME}} — {{TITLE}}

Você é o especialista responsável por {{MISSION}}.
Esta skill é 100% autônoma, autocontida e universal.

`HOME` = pasta onde este `SKILL.md` está.

---

## 0. Contrato de Portabilidade

| Capacidade | Modo Padrão | Fallback Universal |
|---|---|---|
| EXECUÇÃO PRINCIPAL | `python HOME/scripts/{{SCRIPT_NAME}}.py` | Execução manual das etapas em `references/` |
| AUDITORIA & GATES | `python HOME/scripts/{{SCRIPT_NAME}}.py --audit` | Verificação estática de `RULES.md` |
| SINCRONIZAÇÃO | `powershell -File sync.ps1` (Win) / `bash sync.sh` (Unix) | Cópia para `~/.claude/skills/` |

---

## 1. Regras Operacionais e Invariantes

1. **Determinismo Primeiro:** Tarefas locais e mecânicas devem ser resolvidas via scripts locais (custo zero de tokens).
2. **Gates Binários:** Nenhuma fase é concluída sem validação do comando automatizado.
3. **Respeito ao Domínio:** As diretrizes detalhadas devem ser consultadas em `HOME/references/`.
