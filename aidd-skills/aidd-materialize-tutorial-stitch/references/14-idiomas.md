# 14 — Idiomas (narração e legenda em vários idiomas sobre a mesma imagem)

Como nos serviços de streaming: **uma imagem só** (o render sem legenda), **uma faixa de áudio e uma legenda por
idioma**. Padrão: `pt-BR`, `en-US`, `es` (`--idiomas` ou `tutorial.config.json > idiomas`; um idioma só = sem seletor).
Os textos desenhados na animação ficam no idioma original; só a narração e a legenda mudam.

## 1. Quem faz o quê

| Etapa | Quem | Tokens |
|---|---|---|
| traduzir a narração de cada cena (`idiomas/<lang>/traducao.json`, campo `texto`) | **agente** | ~150 palavras por idioma, uma vez |
| voz de cada cena (edge-tts; `en-US-AvaNeural`, `es-MX-DaliaNeural`; `vozes_idioma` no config troca) | script | 0 |
| caber no tempo da cena (acelera só o necessário, até 1,25×; acima disso pede frase mais curta) | script | 0 |
| faixa = narração + os mesmos efeitos da composição, no volume percebido da faixa original | script | 0 |
| legenda `.vtt` com o tempo de cada palavra da voz (nunca parte nome de botão entre aspas) | script | 0 |
| HLS na vitrine (vídeo + faixas de áudio + legendas), seletor no player | script | 0 |

Cache: só refaz a voz de uma cena se o texto, a voz ou o tempo da cena mudarem; a tradução é invalidada sozinha
quando a narração original da cena muda (hash).

## 2. Fluxo (depois do `burn` do T8, ou a qualquer momento num tutorial pronto)

```bash
python HOME/scripts/tutorial.py idiomas <tutorial> --preparar   # cria idiomas/<lang>/traducao.json; sai 3 se falta texto
# agente: preenche só "texto" de cada cena seguindo "regras" do próprio arquivo
python HOME/scripts/tutorial.py idiomas <tutorial>              # voz, faixas, legendas, idiomas/idiomas.json
python HOME/scripts/tutorial.py catalog render <produto>        # refaz a vitrine (e publica, se --auto on)
```

Saída 4 = alguma cena não coube nem a 1,25×: encurte o `texto` daquela cena (a mensagem diz qual) e rode de novo.

Regras de tradução (gravadas no `traducao.json`): sentido e tom do original; **nomes de botões, menus e campos ficam
em português, entre aspas**, como na tela; rótulo longo vira descrição curta no idioma; manter o `|` (quebra de
legenda); frase do mesmo tamanho ou menor.

## 3. Pedido do usuário → comando

| Pedido | Comando |
|---|---|
| "quero em inglês e espanhol também", "põe os idiomas" | `idiomas <tutorial> --preparar` → traduzir → `idiomas <tutorial>` |
| "só em português" / "só em inglês" | `config <tutorial> --idiomas pt-BR` (ou `en-US`) e `idiomas <tutorial>` |
| "troca a voz do espanhol" | `tutorial.config.json > vozes_idioma.es = "<voz>"` e `idiomas <tutorial>` |
| "todos os tutoriais do produto em 3 idiomas" | laço nos itens `gerado` do catálogo; um `catalog render` no fim |

## 4. No player

Botão "Áudio e legendas" no topo: coluna **Áudio** (o original marcado) e coluna **Legendas** (Desligadas + idiomas).
Trocar o áudio leva a legenda junto (se ligada) e o vídeo continua do mesmo ponto. A escolha fica salva no navegador e
vale para o próximo vídeo; na primeira visita vale o idioma do navegador. Sem `idiomas.json`, o tutorial segue com o
mp4 de legenda queimada, como antes.
