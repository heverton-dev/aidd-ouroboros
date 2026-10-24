# AIDD-Social-Reengineer (v1.0.0)

**Dissecador Profundo de Carrosséis, Posts Sociais e Infográficos (Padrão REA).**  
Criada por **Heverton Eduardo Peres (2026)** sob o padrão AIDD / REA + `aidd-lauren`.

---

## 1. Visão Geral

A `aidd-social-reengineer` é o especialista em **engenharia reversa de conteúdo visual e copywriting para redes sociais** (Instagram, LinkedIn, Threads, X).
Ela ingere imagens de slides ou pastas de posts e extrai:
- **Copywriting Slide a Slide:** Transcrição via OCR local com isolamento de títulos, subtítulos e dados.
- **Estrutura Narrativa:** Gancho de atenção (Hook - Slide 1), laço de retenção (Slides 2 a N-1) e chamada para ação (CTA - Slide N).
- **Tokens de Design Visual:** Paleta de contraste, tipografia em caixa alta/baixa, margens e esquema cromático.
- **Contrato Universal REA:** Emite `MANIFEST_REA.json` e `HANDOFF.json` interoperável.

---

## 2. Como Usar

### Dissecação de Carrossel a partir de Pasta de Imagens:
```bash
python scripts/social_reengineer.py --input caminho/para/slides/ --output-dir research/carrossel-estudo/
```

### Diagnóstico de Ambiente:
```bash
python scripts/social_reengineer.py --doctor
```

### Auditoria dos 4 Gates:
```bash
python scripts/social_reengineer.py --audit
```
