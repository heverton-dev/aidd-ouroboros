# 15 — Flags (referência completa)

Carregue só no `init`/`config` ou quando o usuário citar uma flag. Toda flag é gravada em `tutorial.config.json` (`tutorial.py init <pasta> <flags>` / `config`).

| Flag | Valores | Padrão |
|---|---|---|
| `--voz` | `edge[:voz]`, `gemini[:voz]`, `fish[:reference_id]`, `kokoro[:voz]`, `sistema`, `nenhuma`, `gravacao` | `auto` = edge → gemini → kokoro → sistema |
| `--velocidade` | multiplicador da fala | `1.0` |
| `--direcao` | direção de leitura (Gemini): "caloroso, confiante, ritmo médio" | linha `Direção:` do roteiro |
| `--legenda` | `highlight`, `bold-pop`, `word-by-word`, `clean`, `boxed`, `nenhuma` | `highlight` (16:9) / `bold-pop` (9:16) |
| `--caixa` | `normal`, `alta`, `baixa` | `normal` |
| `--legenda-posicao` | `auto` (cada cena longe do foco do passo, calculado do `target_box`), `base`, `meio`, `topo` | `auto` |
| `--legenda-tamanho` | `p`, `m`, `g` | `m` |
| `--acento` | cor da palavra ativa da legenda (hex) | `#FFD43B` |
| `--formato` | `16:9`, `9:16`, `1:1`, `4:5` | `16:9` |
| `--fps` | `24`, `25`, `30`, `50`, `60` | `30` |
| `--duracao` | segundos alvo | do brief |
| `--estilo` | `clean-product`, `glass-3d`, `clay-soft`, `paper-editorial`, `dark-tech` | `clean-product` |
| `--idioma` | `pt-BR`, `en-US`, `es-ES`… | `pt-BR` |
| `--musica` | caminho de trilha local, `nenhuma` | `nenhuma` |
| `--sfx` | `on`, `off` (cliques, whooshes gerados localmente) | `on` |
| `--qualidade` | `rascunho` (render rápido), `final` | `final` |
| `--gates` | `todos`, `essenciais` (só P2, P4, P6), `nenhum` (piloto automático; ainda roda todas as verificações) | `todos` |
| `--canal` | onde o vídeo será usado: `instagram-reels`, `instagram-feed`, `tiktok`, `youtube-shorts`, `youtube`, `plataforma-ensino`, `central-de-ajuda`, `linkedin`, `whatsapp`, `apresentacao` (vírgulas para vários) | — |
| `--formatos` | `16:9`, `9:16`, `1:1`, `4:5` (vírgulas) | o `--formato` |
| `--resolucoes` | `480p`, `720p`, `1080p` (vírgulas) | `1080p` |
| `--responsivo` | `auto` (testa o app no tamanho de cada formato e decide), `sim` (captura nativa em celular/tablet), `nao` (reenquadra a captura desktop) | `auto` |
| `--idiomas` | idiomas de narração e legenda (vírgulas): `pt-BR`, `en-US`, `es` | `pt-BR,en-US,es` |
