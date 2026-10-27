# Manual de Engenharia &bull; Etapa 5: Dissecação REA

> **Raio-X de Arquitetura da Etapa 5 do Ouroboros**  
> Localização no pipeline: `3. VALIDAÇÃO SPEC ➔ 4. ROTEAMENTO ➔ [5. DISSECAÇÃO REA] ➔ 6. SKILLS ➔ 7. PIPELINE ➔ 8. GATES`

---

## 📊 Grau Geral de Automação da Etapa

```
[███████████████████████████████████░░░░░░░░░░░░░░░] 70% Determinístico | 30% Rede/Ambiente
```
- **70% Determinístico**: Extração de tokens, manifests, hashing SHA-256, escrita de relatórios e selagem HMAC.
- **30% Rede/Ambiente**: Fetch de URL, download de vídeo, OCR local (tesseract) e fallbacks quando binários/rede falham.

---

## 1. Input da Etapa (O que entra e de onde vem)

| Dado | Tipo | Exemplo | Origem |
| :--- | :--- | :--- | :--- |
| Alvo de engenharia reversa | `string` | `https://example.com` | Etapa 4 (router) |
| `--output-dir` | `Path` abs. | `OUT/rea` | Mestra |
| `--output-handoff` | `Path` abs. | `OUT/handoffs/01_rea_handoff.json` | Mestra |
| Binários opcionais | `system` | `ffmpeg`, `yt-dlp`, `tesseract` | Ambiente |
| Chave HMAC | `env` | `OUROBOROS_CRYPTO_SECRET` | `.env` |

---

## 2. Processamento Passo a Passo (Microações e Natureza)

### Ação 5.1: Abertura e normalização do alvo
- **O que faz**: Conforme tipo: HTTP fetch, abertura de APK/zip, leitura de imagens ou aquisição de vídeo/metadata.
- **Natureza**: `50% Determinístico / 50% Rede` (web/vídeo) ou `100% Determinístico` (APK local).

### Ação 5.2: Extração de evidências (microação por família)
- **O que faz**:
  - **Web**: tokens de design, `conteudo_tecnico.md`, `estrutura_ux.md`, `MANIFEST_REA.json`.
  - **APK**: package, permissões, activities, endpoints + manifesto.
  - **Vídeo**: metadata, metodologia, evidências visuais.
  - **Social**: OCR slide a slide, paleta, hook/CTA, manifesto.
- **Natureza**: `90% Determinístico / 10% Fallback de rede ou OCR`.

### Ação 5.3: Selo do envelope REA
- **O que faz**: `emit_handoff_hmac` → `criar_envelope_handoff` com ponteiros `{path, sha256, tamanho_bytes}` e `domain_metadata` do alvo.
- **Natureza**: `100% Determinístico` (HMAC-SHA256 + SHA-256 de arquivos).

### Ação 5.4: Publicação no workspace da F2
- **O que faz**: Escreve artefatos sob `OUT/rea/**` e handoff em `OUT/handoffs/01_rea_handoff.json` (caminhos absolutos).
- **Natureza**: `100% Determinístico`.

---

## 3. Scripts, Funções e Regras no Código

- **Web**: `aidd-rea-web-saas/scripts/web_reengineer.py` &bull; `dissect_web_application`, `emit_handoff_hmac`.
- **APK**: `aidd-rea-app-android/scripts/app_reengineer.py` &bull; `dissect_mobile_or_binary_app`.
- **Vídeo**: `aidd-rea-video-youtube/scripts/video_reengineer.py` &bull; `generate_evidence_manifest`.
- **Social**: `aidd-rea-social-carousel/scripts/social_reengineer.py` &bull; `dissect_social_carousel`, `ocr_image_file`.
- **Motores**: `handoff_crypto.criar_envelope_handoff`, `credentials.carregar_env_local`.
- **Regra**: envelope canônico `{body, seal}` — proibido legado flat `handoff-v1` sem assinatura.

---

## 4. O que a Etapa Entrega, Para Quem e Como?

| O que entrega | Para quem entrega | Como entrega (Formato / Meio) |
| :--- | :--- | :--- |
| **Tokens / relatórios / manifesto** | Usuário e etapas seguintes | Arquivos em `OUT/rea/**` (JSON + Markdown) |
| **Handoff assinado da REA** | Mestra (Etapa 4/6) e pipelines | `OUT/handoffs/01_rea_handoff.json` (HMAC verificável) |
| **Ponteiros com hash** | Auditoria forense | `body.artifacts_pointers[*].sha256` |
| **Dados do domínio** | Downstream / humano | `body.domain_metadata` (ex.: permissões do APK) |
