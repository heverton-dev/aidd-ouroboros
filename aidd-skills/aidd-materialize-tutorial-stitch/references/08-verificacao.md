# 08 — Verificação (todas as fases com render)

"Nada vai para o usuário sem ter sido olhado." A verificação combina checagens automáticas e inspeção dos stills pelo agente.

## 1. Automáticas

| Quando | Comando | Passa se |
|---|---|---|
| T5 | `python HOME/scripts/tutorial.py audit storyboard tutorials/<slug>` | 0 erros (avisos explicados ao usuário) |
| T5, T8 | `python HOME/scripts/tutorial.py audit captions tutorials/<slug>` | nenhum bloco de legenda cobre `target_box` (com zoom) ou `focus_boxes`, no mestre e em cada saída |
| T6, T7 | `python HOME/scripts/tutorial.py audit brand tutorials/<slug>` | nenhuma cor (hex ou `rgb()`) nem fonte fora do `design-tokens.json` do produto |
| T6, T7 | `python HOME/scripts/tutorial.py audit composition tutorials/<slug>` | cenas cobertas, `<audio>` com id, arquivos existem, sem relógio/aleatório, `timeline.js` em dia; com `compose.json`: nenhum destaque cobre o clique, nada fora do quadro, cliques ancorados na fala |
| T6–T8 | `python HOME/scripts/tutorial.py audit privacy tutorials/<slug>` | nenhum e-mail, CPF/CNPJ, telefone ou token fora dos fictícios permitidos |
| T6, T7 | `npx hyperframes check --json` (no diretório `composition/`) | 0 erros; avisos de contraste e overflow resolvidos ou justificados |
| T7 | `npx hyperframes check --json --at-transitions` | sem sobreposição transitória nas emendas |
| T8 | `python HOME/scripts/tutorial.py audit final tutorials/<slug>` | 0 erros |

`audit final` verifica, além do storyboard: o render existe; a duração do MP4 (ffprobe) bate com `meta.duration` (±0,5 s); resolução e fps batem com o brief; existe faixa de áudio quando há narração; `.srt` existe, tem cues, termina antes do fim do vídeo e cobre a narração; nenhum arquivo de evidência referenciado sumiu.

## 2. Inspeção dos stills (agente)

Com composição gerada pelo `compose`, os itens 2 (parcial), 4, 6 (texto) e 7 abaixo já são checados pelos audits
acima: olhe só o que é gosto e pixel (1, 3, 5, 8), em quadros reduzidos (`tutorial.py frames <render> --at …`, 800 px).

Gere: `npx hyperframes snapshot --review -o ../snapshots/review` (cada cena em início + 0,3 s e no meio). Para cada still, responda sim/não:
1. Todo texto está **dentro do quadro**, sem corte, com margem ≥ 4 % das bordas?
2. Nenhum elemento **sobrepõe** texto (callout sobre rótulo, cursor sobre palavra-chave, logo sobre legenda)?
3. Texto **grande o bastante** (≥ 28 px a 1080p; ≥ 40 px em 9:16) e com contraste AA?
4. O zoom/cursor/callout está no **elemento certo** do passo (`target_box`)?
5. A tela mostrada corresponde à evidência do passo (mesmo estado)?
6. **Nenhum dado sensível** visível (e-mail, token, nome real, valor de cliente)?
7. Tudo que foi desenhado por cima da tela (callout, chip, selo) está declarado em `focus_boxes`, e `screen_box`/`zoom` do storyboard batem com a composição? (A colisão em si é checada pelo `audit captions`.)
8. O estilo é coerente com o piloto aprovado (cor, fonte, raio, sombra)?

Qualquer "não" → corrigir antes de renderizar. Registre a causa em `rules.md` > Lições se for um erro que pode se repetir.

## 3. Sincronia

- Assista mentalmente pelo storyboard: cada clique acontece **durante ou logo depois** da frase que o descreve, nunca antes.
- Se a duração de alguma fala mudou (novo TTS, edição), rode de novo `tutorial.py tts` e `audit storyboard`; nunca empurre os tempos à mão sem atualizar o `storyboard.json`.
- Mudança de velocidade no áudio exige recalcular **todos** os timestamps (lição registrada na metodologia: 5 % de diferença dessincroniza o vídeo inteiro).

## 4. Auditoria de cobertura (estilo roteiro × transcrição × timeline)

Quando a narração foi gravada pelo usuário (ou editada), transcreva o áudio final e compare com `script.md`:
```bash
python HOME/scripts/tutorial.py audit coverage tutorials/<slug> --transcript audio/narration.transcript.json
```
Cada frase do roteiro deve aparecer **exatamente uma vez**; repetição (retake) ou ausência é sinalizada com o tempo. A transcrição "limpa" gaguejos; por isso o roteiro é a fonte da verdade e a transcrição é só evidência.

## 5. Veredito

Ao entregar: VERIFIED (tudo passou), VERIFIED WITH CAVEATS (o que não foi verificado e por quê) ou REFUTED (o que falhou). Anexe os caminhos de `snapshots/review/` e a saída dos audits.
