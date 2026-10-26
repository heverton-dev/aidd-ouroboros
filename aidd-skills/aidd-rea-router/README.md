# AIDD-REA-Router (v1.0.0)

**Roteador Universal e Classificador de Alvos REA.**  
Criada por **Heverton Eduardo Peres (2026)** sob o padrão AIDD / REA + `aidd-lauren`.

---

## 1. Visão Geral

A `aidd-rea-router` é a **porta de entrada única** para todo o ecossistema de engenharia reversa do projeto.
Em vez de o usuário precisar saber qual ferramenta chamar, o roteador analisa a entrada e delega para o especialista correto:
- **Vídeo (YouTube, TikTok, Reels, MP4):** $\rightarrow$ `aidd-rea-video-youtube`
- **Web App, Landing Page, SaaS (HTTP/HTTPS):** $\rightarrow$ `aidd-rea-web-saas`
- **Carrosséis, Infográficos, Posts Sociais:** $\rightarrow$ `aidd-rea-social-carousel`
- **Aplicativos Android (APK), Binários Nativos:** $\rightarrow$ `aidd-rea-app-android`

---

## 2. Como Usar

### Roteamento Automático de Qualquer Entrada:
```bash
python scripts/rea_router.py --target "https://www.youtube.com/watch?v=..."
python scripts/rea_router.py --target "https://meusaas.com"
python scripts/rea_router.py --target "caminho/para/carrossel/"
python scripts/rea_router.py --target "app-release.apk"
```

### Apenas Classificar sem Executar:
```bash
python scripts/rea_router.py --classify "https://exemplo.com"
```

### Diagnóstico de Ambiente:
```bash
python scripts/rea_router.py --doctor
```

### Auditoria dos 4 Gates:
```bash
python scripts/rea_router.py --audit
```
