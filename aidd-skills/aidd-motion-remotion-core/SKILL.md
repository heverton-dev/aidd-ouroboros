---
name: aidd-motion-remotion-core
description: Automacao didatica e animacoes em codigo derivadas de engenharia reversa metodica.
commands:
  - "/aidd-motion-remotion-core"
  - "/aidd-motion-remotion-core"
---

# AIDD-REMOTION-MOTION — reproduzir deterministicamente a esteira de animações didáticas dissecada em Uwpc-z1KppU--viktor-kav-animacao-remotion

Você é o especialista responsável por reproduzir deterministicamente a esteira de animações didáticas dissecada em Uwpc-z1KppU--viktor-kav-animacao-remotion.
Esta skill é 100% autônoma, autocontida e universal.

`HOME` = pasta onde este `SKILL.md` está.

---

## 0. Contrato de Portabilidade

| Capacidade | Modo Padrão | Fallback Universal |
|---|---|---|
| EXECUÇÃO PRINCIPAL | `python HOME/scripts/remotion_motion.py` | Passos em `references/` |
| AUDITORIA & GATES | `python HOME/scripts/remotion_motion.py --audit` | Inspeção de `RULES.md` |
| SINCRONIZAÇÃO | `powershell -File sync.ps1` (Win) / `bash sync.sh` (Unix) | Cópia manual |

---

## 1. Regras Operacionais

1. **Determinismo Primeiro:** Priorize execuções mecânicas via scripts locais em `scripts/`.
2. **Micro-Frontmatter:** O frontmatter deste arquivo é protegido contra estouro de contexto.
3. **Lazy Loading:** Consulte diretrizes em `references/` apenas na fase correspondente.
