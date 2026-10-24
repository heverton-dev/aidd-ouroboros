# 01 — Entrevista (T1)

Objetivo: fechar o brief com o mínimo de perguntas. Pergunte **só o que não dá para inferir** do pedido e do alvo. No máximo 5 perguntas, numa única rodada, cada uma com uma resposta recomendada.

## Perguntas (na ordem; pule as já respondidas)

1. **Objetivo e público.** O que a pessoa deve conseguir fazer ao fim do vídeo, e quem é ela (cliente novo, usuário avançado, time interno)?
   Recomendado: "um usuário novo consegue completar a tarefa principal da tela sozinho".
2. **Escopo do fluxo.** Quais passos entram (do clique inicial ao resultado)? Se o usuário não souber, proponha a lista a partir de uma captura rápida e peça confirmação no gate P2.
3. **Duração e formato.**
   - Duração: 15 s (teaser), 30 a 45 s (padrão para um fluxo), 60 a 90 s (fluxo com 5 a 8 passos), até 3 min (tutorial completo; considerar dividir em capítulos).
   - Formato: 16:9 1920×1080 (YouTube, docs, site), 9:16 1080×1920 (Shorts, Reels, TikTok), 1:1 1080×1080 (feed, LinkedIn).
   - fps: 30 (padrão para UI), 60 (se houver muito movimento de câmera).
   Recomendado: 45 s, 16:9, 30 fps.
4. **Voz e idioma.** Narração com TTS local (padrão), voz do próprio usuário (ele grava a partir do roteiro) ou sem voz (só texto + música). Idioma da narração e das legendas.
   Recomendado: TTS local em pt-BR + legendas pt-BR + `.srt`.
5. **Estilo.** Marca do produto (cores, fonte, logo), uma referência visual (link do YouTube, imagem, site) ou um estilo nomeado: `clean-product` (padrão), `glass-3d`, `clay-soft`, `paper-editorial`, `dark-tech`. Ver `07-build-render.md` > Estilos.
   Recomendado: `clean-product` com as cores do próprio app.

## Perguntas condicionais (só quando o alvo exigir)

- Área autenticada: "Você abre o Chrome com `--remote-debugging-port=9222` e faz login? Eu me conecto a ele sem tocar na sua senha."
- Ações que gravam dados: "Posso executar estas ações nesta conta/ambiente: <lista>?"
- Dados reais na tela: "Substituo nomes, e-mails e valores por fictícios?" (padrão: sim)
- Música: "Trilha de fundo? (nenhuma / fornecida por você / gerada localmente)"

## Saída: `brief.md`

```markdown
# Brief — <título do tutorial>
- Alvo: <URL / app / pacote / vídeo> (tipo: <APP WEB | SITE | ELECTRON | DESKTOP NATIVO | ANDROID | iOS | VÍDEO>)
- Base de autorização: <produto próprio | conta própria | site público | direito de uso>
- Objetivo: <o que a pessoa consegue fazer ao fim>
- Público: <quem>
- Fluxo: <passo 1 → passo 2 → … → resultado>
- Duração: <s>  Formato: <1920x1080 | 1080x1920 | 1080x1080>  fps: <30|60>
- Voz: <tts:<voz> | gravação própria | sem voz>  Idioma: <pt-BR>  Legendas: <sim/não> (.srt: sim)
- Estilo: <nomeado | marca | referência: <link>>
- Restrições: <dados fictícios, ações proibidas, prazos>
```

Gate **P1**: o usuário aprova o brief (ou responde "ok"). Sem aprovação, não capture.
