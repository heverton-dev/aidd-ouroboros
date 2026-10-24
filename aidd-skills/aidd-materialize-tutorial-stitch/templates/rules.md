# Regras do projeto

Lido no início de toda execução e anexado ao prompt mestre. Regras aqui vencem o prompt.

## Congelado
<!-- cenas e componentes aprovados; não alterar sem pedido explícito -->
- (vazio)

## Lições
<!-- cada erro corrigido vira uma regra curta e verificável, com a causa -->
- Regerar `audio/durations.json` e rodar `audit storyboard` sempre que a narração ou a velocidade do TTS mudar.
- Nunca remover a faixa de narração ao reconstruir uma cena.
- Callout nunca cobre o elemento que está sendo clicado.
- Mostrar a tela "antes" durante a ação e a tela "depois" só no clique (o REA captura depois de cada passo).
- Clique do cursor no instante em que a narração diz o rótulo (`audio/<cena>.words.json`).
- Voz do sistema (SAPI/say/espeak) é robótica: usar edge ou gemini.
- Todo `<audio>` com `id`, senão o render sai mudo.
- Renderizar com `tutorial.py render` (TEMP local) e queimar legenda com `tutorial.py burn`.
- No mestre 16:9, todo conteúdo importante (inclusive selos e etiquetas) fica entre x 320 e 1600: fora disso é cortado no reenquadramento.
- Em composição nativa vertical, o chip de passo mora numa faixa de cabeçalho; nada solto por cima da tela do app.

## Preferências do usuário
- (vazio)
