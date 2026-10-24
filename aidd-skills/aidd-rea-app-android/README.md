# AIDD-App-Reengineer (v1.0.0)

**Dissecador Profundo de Aplicativos Mobile (Android APK) e Binários Nativos (Padrão REA).**  
Criada por **Heverton Eduardo Peres (2026)** sob o padrão AIDD / REA + `aidd-lauren`.

---

## 1. Visão Geral

A `aidd-app-reengineer` é o especialista do ecossistema AIDD dedicado à **engenharia reversa e dissecação de aplicativos móveis (arquivos .apk) e binários executáveis**.
Ela realiza análise estática e extração de:
- **Manifesto e Metadados:** Nome do pacote, versão, permissões requisitadas, activities (telas) e services.
- **Strings de Negócio:** Mensagens de interface, chaves de tradução e textos de conversão.
- **Endpoints de Rede:** URLs e rotas de API embutidas no código ou assets.
- **Design Tokens Nativos:** Cores de tema e estilos visuais do aplicativo.
- **Contrato Universal REA:** Emite `MANIFEST_REA.json` e `HANDOFF.json` interoperável.

---

## 2. Como Usar

### Dissecação de APK ou Pacote:
```bash
python scripts/app_reengineer.py --input app-release.apk --output-dir research/app-target/
```

### Diagnóstico de Ambiente:
```bash
python scripts/app_reengineer.py --doctor
```

### Auditoria dos 4 Gates:
```bash
python scripts/app_reengineer.py --audit
```
