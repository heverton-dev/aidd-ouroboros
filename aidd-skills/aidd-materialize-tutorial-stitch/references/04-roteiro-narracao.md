# 04 — Roteiro e narração, voz primeiro (T4)

Objetivo: escrever a narração **antes** das cenas, gerar a voz e medir a duração real de cada trecho. O áudio vai mandar no tempo; o roteiro vai mandar no conteúdo.

## 1. Orçamento de palavras

- Regra: **~2,5 palavras por segundo** (25 palavras a cada 10 s) para narração clara de tutorial. Em pt-BR, use 2,3 a 2,6; para público técnico apressado, até 2,8.
- `python HOME/scripts/tutorial.py timing tutorials/<slug>/script.md --wps 2.5` mostra palavras, segundos estimados por cena e o total contra a duração do brief.
- Deixe **0,3 a 0,6 s de respiro** depois de cada ação na tela (o clique precisa ser visto antes da próxima frase).

## 2. Estrutura do roteiro de tutorial

1. **Gancho (2 a 4 s)**: o resultado que a pessoa vai conseguir. "Em 40 segundos, você gera seu primeiro relatório."
2. **Contexto (opcional, até 4 s)**: onde estamos. "Tudo começa na aba Relatórios."
3. **Passos (o corpo)**: um bloco por passo do `step-map.json`, sempre **verbo de ação + alvo visível + resultado**. "Clique em Período e escolha Últimos 30 dias. A tabela se atualiza na hora."
4. **Resultado (2 a 4 s)**: mostrar o estado final.
5. **Fecho / CTA (2 a 3 s)**: próximo passo ou onde saber mais.

Regras de texto:
- Use **exatamente** os rótulos da interface (do `ui_text` da evidência), entre aspas tipográficas quando ajudar: “Exportar”.
- Uma ideia por frase; frases de até 14 palavras.
- Segunda pessoa, presente, voz ativa. Nada de "simplesmente" ou "basta".
- Números e siglas como serão falados ("trinta dias", não "30d"), mas as legendas mostram a forma escrita.

## 3. Formato do arquivo `script.md`

Um bloco por cena planejada; o `id` vira o id da cena no storyboard.

```markdown
# Roteiro — <título>

## c01 — Gancho
Em quarenta segundos, você gera seu primeiro relatório no Painel.

## c02 — Abrir relatórios
Tudo começa na aba “Relatórios”, no menu da esquerda.

## c03 — Filtrar período  [steps: s03]
Clique em “Período” e escolha “Últimos 30 dias”. A tabela se atualiza na hora.
```

- Cabeçalho: `## <id> — <título>`; opcional `[steps: s01, s02]` liga a cena aos passos do `step-map.json`.
- `|` dentro da narração força a quebra do bloco de legenda naquele ponto (`A tabela | se atualiza na hora.`). O `tts` remove o marcador antes de falar e grava `"brk": true` na palavra anterior em `audio/<id>.words.json`. Use para não separar nome de produto e verbo, ou para dar ritmo a frases longas.
- Linhas que começam com `<!--` ou `>` (notas de direção) não contam como narração.
- **Direção de leitura** numa linha no topo: `Direção: caloroso, confiante, ritmo médio, pausa curta entre frases.`

## 4. Gerar a voz

```bash
python HOME/scripts/tutorial.py tts tutorials/<slug>/script.md          # usa a flag --voz gravada no tutorial.config.json
python HOME/scripts/tutorial.py tts tutorials/<slug>/script.md --engine gemini --voice Charon   # sobrescreve
```
Gera `audio/<id>.wav` por cena, `audio/<id>.words.json` (tempo de cada palavra, base das legendas e da sincronia do cursor), `audio/durations.json` e `audio/voice.json`.

| Motor (`--engine` / flag `--voz`) | Qualidade | Custo / requisito | Observações |
|---|---|---|---|
| `edge` (padrão do `auto`) | neural, natural | grátis, sem chave; pacote `edge-tts` | vozes pt-BR: `pt-BR-FranciscaNeural`, `pt-BR-AntonioNeural`, `pt-BR-ThalitaMultilingualNeural`. Devolve o **tempo exato de cada palavra**; a pontuação é recuperada do roteiro. **Envia o texto da narração ao serviço online da Microsoft** (avise se o roteiro for confidencial). Erro 403 = pacote desatualizado: `pip install -U edge-tts` (peça OK) |
| `gemini` | muito expressiva; segue a direção de leitura | grátis no Google AI Studio com `GEMINI_API_KEY` (aistudio.google.com > Get API key); pacote `google-genai` | vozes: `Kore`, `Charon`, `Puck`, `Aoede`, `Fenrir`… Modelo por `--model` ou `TC_GEMINI_TTS_MODEL`. Tempos por palavra via Whisper local. Envia o texto ao Google |
| `fish` | alta, com clonagem de voz | `FISH_API_KEY` (fish.audio; plano grátis limitado); `--voice` = `reference_id` do modelo | modelo por `TC_FISH_MODEL` (padrão `s1`) |
| `kokoro` | boa, 100 % local | `pip install kokoro-onnx soundfile` (peça OK) | via `npx hyperframes tts`; vozes `npx hyperframes tts --list`, `--lang pt-br` |
| `system` | **robótica** | nenhum | SAPI (Windows, "Microsoft Maria Desktop"), `say` (macOS), `espeak-ng` (Linux). Só como último recurso; o teste de validação reprovou a qualidade |

`auto` tenta edge → gemini → kokoro → system e avisa a cada queda. Motor explícito não cai para outro: falha com a causa.

### Catálogo de vozes e escolha pelo usuário
```bash
python HOME/scripts/tutorial.py voices <pasta> --motores edge,gemini,system --amostras --texto "frase com o nome do produto"
```
Gera `VOZES.md` (motor, voz, gênero, caráter, idioma, link da amostra e a flag pronta) e `amostras/*.mp3` (uma frase curta por voz). Mostre ao usuário, deixe ouvir, e grave a escolha: `tutorial.py config <projeto> --voz edge:pt-BR-AntonioNeural` (registrada no `ESTADO.md`). Notas:
- edge: as 3 vozes nativas pt-BR (Antonio, Francisca, Thalita) e as **multilíngues** de outros idiomas (Andrew, Ava, Emma, Brian…), que falam português com leve sotaque.
- gemini: 30 vozes com caráter (calorosa, firme, informativa, animada…); sem `GEMINI_API_KEY` o catálogo lista as vozes e marca que as amostras precisam da chave.
- No modo catálogo, gere o `VOZES.md` uma vez em `compartilhado/vozes/`.

Depois da voz, **sempre**:
```bash
python HOME/scripts/tutorial.py retime tutorials/<slug> --gap 0.3      # start/end das cenas a partir das durações reais
python HOME/scripts/tutorial.py narration tutorials/<slug>             # audio/narration.wav na linha do tempo
python HOME/scripts/tutorial.py audit storyboard tutorials/<slug>
```
No teste de validação, a voz neural (edge) durou 14,5 s para 14,4 s estimados; a SAPI durou 21 s. A estimativa serve para o roteiro, a duração medida manda no storyboard.

Ajuste até caber:
- Longo demais: corte palavras antes de acelerar; depois `--speed 1.05` a `1.1`.
- Curto demais: estenda o respiro visual (não encha de palavras).

Outras opções:
- **Voz do usuário**: entregue `script.md` como teleprompter; ele grava `audio/narration.wav`; transcreva com `npx hyperframes transcribe audio/narration.wav --json` para obter os timestamps por palavra e alinhe as cenas a eles.
- **Sem voz**: as durações vêm do texto na tela (mín. 1,2 s + 0,3 s por palavra visível) e da música.

## 5. Durações finais

`audio/durations.json` (ou os timestamps da transcrição) define `start`/`end` de cada cena em T5:
`duração_da_cena = duração_da_fala + respiro (0,3 a 0,6 s) + tempo de ação visual extra, se houver`.

Gate **P3**: o usuário ouve a narração de rascunho (ou lê o roteiro) e aprova texto, voz e duração total (±10 % do brief).
