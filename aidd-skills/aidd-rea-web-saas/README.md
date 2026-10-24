# AIDD-Web-Reengineer (v1.0.0)

**Dissecador Profundo de Aplicações Web, SaaS e Landing Pages (Padrão REA).**  
Criada por **Heverton Eduardo Peres (2026)** sob o padrão AIDD / REA + `aidd-lauren`.

---

## 1. Visão Geral

A `aidd-web-reengineer` é o especialista do ecossistema AIDD dedicado à **engenharia reversa profunda de sites, landing pages e plataformas SaaS**. 
Ela consome uma URL de entrada e extrai cirurgicamente:
- **Tokens de Design (Design Tokens):** Paleta de cores computada (primária, fundo, texto, acentos), tipografia, escalas e raios de borda.
- **Estrutura Técnica:** Stack de frontend detectada, formulários, rotas e endpoints de API observados.
- **Estrutura de UX e Conversão:** Hierarquia visual de seções, chamadas para ação (CTAs), propostas de valor e fluxo do usuário.
- **Captura Visual:** Screenshots em Desktop (1920x1080) e Mobile (375x812).
- **Contrato Universal REA:** Emite `MANIFEST_REA.json` e `HANDOFF.json` prontos para consumo por criadores de skills e pipelines.

---

## 2. Como Usar

### Dissecação Completa de URL:
```bash
python scripts/web_reengineer.py https://exemplo.com --output-dir research/web-exemplo
```

### Extração em Pipeline (com Handoff de Saída):
```bash
python scripts/web_reengineer.py https://exemplo.com --output-handoff context/handoffs/01_web_evidence.json
```

### Diagnóstico de Ambiente:
```bash
python scripts/web_reengineer.py --doctor
```

### Auditoria dos 4 Gates:
```bash
python scripts/web_reengineer.py --audit
```
