# 02 — Aquisição de Áudio, Vídeo e Extração de Frames

## 1. Aquisição com `yt-dlp`
Para permitir a leitura nítida de textos pequenos de código, terminais e editores de vídeo, o download deve priorizar fluxos de até 1080p sem compressão excessiva:

```bash
yt-dlp -f "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best" --recode-video mp4 -o "video.mp4" "<URL>"
```

Para a esteira de áudio:
```bash
yt-dlp -x --audio-format mp3 -o "audio.mp3" "<URL>"
```

## 2. Transcrição Cronometrada (`faster-whisper`)
A transcrição fonética precisa gerar marcas de tempo no formato `[mm:ss]` para permitir alinhamento cruzado com os frames:
- Utilizar modelo `small` ou `medium` com `vad_filter=True` para eliminar silêncios.
- Gravar em formato delimitado por tabulação (`transcript.tsv`) para busca rápida via scripts.

## 3. Extração Cirúrgica de Frames (`ffmpeg`)
- **Amostragem Cronometrada:** Ideal para visões gerais (ex: 1 frame a cada 10 ou 15 segundos).
- **Detecção de Mudança de Cena:** `ffmpeg -i video.mp4 -vf "select='gt(scene,0.3)',scale=1920:-1" -vsync vfr scene_%03d.png`. Captura exatamente as viradas de tela onde novos prompts ou abas são abertos.
