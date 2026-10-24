# 04 — Conector com aidd-video-reengineer

A flag `--from-video-reengineer <caminho>` integra a esteira de engenharia reversa diretamente à fábrica de skills:

```text
[Vídeo YouTube] 
       ↓ (aidd-video-reengineer)
[metodologia.md + prompts + tokens]
       ↓ (aidd-skill-creator --from-video-reengineer)
[Nova Skill Pronta no Padrão Enterprise]
```

## Como o Conector Opera:
1. Localiza o arquivo `metodologia.md` da pasta do vídeo.
2. Extrai os princípios técnicos, os prompts mestres e os presets de configuração.
3. Transforma esses achados em módulos para a nova skill:
   - Os prompts viram `templates/PROMPTS_MESTRES.md`.
   - As regras didáticas viram `references/00-metodologia.md`.
   - Os presets visuais viram `templates/TOKENS.json`.
   - Gera o `SKILL.md` com Micro-Frontmatter e compila o scaffolding completo.
