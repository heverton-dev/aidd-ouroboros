# AIDD-Skill-Creator (v1.0.0)

**Meta-Skill Enterprise Autônoma para Geração, Padronização e Migração de Skills.**  
Criada por **Heverton Eduardo Peres** sob o padrão AIDD / REA + `aidd-lauren`.

---

## 1. Visão Geral

A `aidd-skill-creator` resolve o problema da criação artesanal ou amadora de skills de IA. Ela gera módulos 100% autocontidos, agnósticos a qualquer harness (Claude Code, Antigravity, Cursor, OpenCode, Hermes) e com proteção ativa de tokens no System Prompt via **Micro-Frontmatter**.

---

## 2. Capacidades Principais

* **Entrevista Socrática Embutida:** Questionário cirúrgico (estilo Matt Pocock e Addy Osmani) para transformar qualquer ideia em um contrato executável (`SPEC_SKILL.json`).
* **Conector com Vídeos (`--from-video-reengineer`):** Transforma metodologias de vídeos dissecadas pela skill `aidd-video-reengineer` em novas skills completas em segundos.
* **Micro-Frontmatter Linter:** Garante que o cabeçalho do `SKILL.md` tenha no máximo 25 palavras, evitando que catálogos de 50+ skills estourem a janela de contexto do system prompt.
* **Auditor com Circuit Breakers (`--audit`):** Verifica 4 gates binários de conformidade.
* **Sincronização Multi-Harness (`sync.ps1` / `sync.sh`):** Propaga a nova skill instantaneamente para 13 pastas da máquina.

---

## 3. Como Usar

### Instalação e Setup One-Liner:
```bash
python scripts/skill_creator.py --setup
```

### Criar Skill via Entrevista Socrática:
```bash
python scripts/skill_creator.py --nome "minha-nova-skill" --autor "Heverton Eduardo Peres" --modo socratic
```

### Criar Skill Diretamente de uma Metodologia de Vídeo:
```bash
python scripts/skill_creator.py --nome "aidd-remotion-motion" --autor "Heverton Eduardo Peres" --from-video-reengineer "research/videos/Uwpc-z1KppU--viktor-kav-animacao-remotion"
```

### Auditar Conformidade e Orçamento de Tokens de uma Skill:
```bash
python scripts/skill_creator.py --audit "caminho/para/qualquer-skill"
```
