# AGENTS.md — Contrato de Governança para Agentes (aidd-skill-creator)

Diretrizes para agentes de IA operando a meta-skill `aidd-skill-creator`.

---

## 1. Leis de Construção de Novas Skills

1. **Economia Rígida de Tokens:**  
   Nunca escreva descrições longas no frontmatter do `SKILL.md`. Use no máximo 25 palavras. Se precisar explicar a skill em detalhes, use o corpo do Markdown ou `references/`.
2. **Padrão Dual-Spec Obrigatório:**  
   Toda skill gerada deve conter tanto `SKILL.md` quanto `AGENTS.md`.
3. **Autocontenção:**  
   A nova skill deve conter seu próprio `LICENSE` (MIT), `pyproject.toml`, `requirements.txt`, `sync.ps1` e `sync.sh`.
4. **Gates e Auditor:**  
   Toda skill gerada deve ter seu script de execução com suporte a `--audit` e Circuit Breakers.
5. **Aprovação Prévia do SPEC:**  
   Nunca gere arquivos no disco antes do usuário aprovar o resumo do `SPEC_SKILL.json`.
6. **Prioridade ao Open-Source (GitHub Scout):**  
   Antes de criar uma nova skill do zero, utilize `python scripts/skill_creator.py --github-scout <termo>` para localizar projetos de ponta no GitHub, refatorando-os com proveniência e prefixo proprietário `aidd-`.

