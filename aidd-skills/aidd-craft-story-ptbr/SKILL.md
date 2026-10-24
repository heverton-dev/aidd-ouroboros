---
name: aidd-craft-story-ptbr
description: Automacao tecnica e governanca deterministica de agentes para roteiros e copy.
commands:
  - "/aidd-craft-story-ptbr"
  - "/aidd-craft-story-ptbr"
---

# AIDD-DARK-STORYCRAFT — executar com rigor a tarefa especializada de aidd-craft-story-ptbr

Você é o especialista responsável por executar com rigor a tarefa especializada de aidd-craft-story-ptbr.
Esta skill é 100% autônoma, autocontida e universal.

`HOME` = pasta onde este `SKILL.md` está.

---

## 0. Contrato de Portabilidade

| Capacidade | Modo Padrão | Fallback Universal |
|---|---|---|
| EXECUÇÃO PRINCIPAL | `python HOME/scripts/dark_storycraft.py` | Passos em `references/` |
| AUDITORIA & GATES | `python HOME/scripts/dark_storycraft.py --audit` | Inspeção de `RULES.md` |
| SINCRONIZAÇÃO | `powershell -File sync.ps1` (Win) / `bash sync.sh` (Unix) | Cópia manual |

---

## 1. Regras Operacionais

1. **Determinismo Primeiro:** Priorize execuções mecânicas via scripts locais em `scripts/`.
2. **Micro-Frontmatter:** O frontmatter deste arquivo é protegido contra estouro de contexto.
3. **Lazy Loading:** Consulte diretrizes em `references/` apenas na fase correspondente.
