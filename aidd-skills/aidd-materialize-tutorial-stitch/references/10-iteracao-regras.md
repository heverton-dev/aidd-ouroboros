# 10 — Iteração travada e regras do projeto (T9)

## 1. Como o usuário pede mudanças

O usuário assiste ao render e fala em linguagem natural ("esta cena está rápida", "não gostei desta transição", "a imagem não combina"). Ele pode apontar por tempo, por id de cena, ou mandar um screenshot.

Para cada pedido:
1. Localize a(s) cena(s) afetada(s) no `storyboard.json` (por tempo ou id).
2. Diga em 1 linha **como** vai corrigir e **o que fica intocado** ("ajusto só a velocidade da c04 de 4,2 para 5,0 s; c01 a c03 e c05 a c08 ficam como estão").
3. Espere o OK quando a mudança afeta tempo, estilo global ou mais de uma cena; mudanças locais e óbvias podem seguir direto.
4. Aplique o delta, rode `audit storyboard` (se mudou tempo), `hyperframes check` e snapshots só das cenas tocadas; renderize de novo.

Nunca reescreva a composição inteira para atender um ajuste local. Nunca recomece do zero.

## 2. `rules.md` do projeto

Arquivo lido no início de **toda** execução do projeto e anexado ao prompt mestre. Modelo em `templates/rules.md`. Como é relido sempre, fica **curto (até ~40 linhas)**: lição repetida vira uma só, e lição que virou checagem de script (`audit …`) sai do arquivo e fica só no script. Três seções:

- **Congelado**: cenas e componentes aprovados que não podem mudar sem pedido explícito (ex.: "c01 aprovada em 2026-10-21; não alterar").
- **Lições**: cada erro corrigido vira uma regra curta e verificável, com a causa. Exemplos:
  - "Sempre regenerar `durations.json` depois de mudar a velocidade do TTS; uma mudança de 5 % dessincronizou todas as cenas."
  - "Nunca remover a faixa de áudio da narração ao reconstruir uma cena."
  - "Callout nunca sobre o botão que está sendo clicado; ancorar acima ou à esquerda."
  - "PiP com borda suave (raio 24 px, sombra) e entrada em 0,5 s; a borda dura pareceu datada."
- **Preferências do usuário**: gosto declarado ("prefere cortes secos", "odeia texto em caixa alta").

## 3. Reaproveitamento

Ao criar um novo tutorial do **mesmo produto**, copie `blueprint.md`, os componentes compartilhados e o `rules.md` do projeto anterior: o segundo vídeo sai mais rápido e sem os erros do primeiro. Registre em `ESTADO.md` de qual projeto veio a base.

## 4. Gate final P6

O usuário aceita a versão. Grave em `ESTADO.md`: versão aceita, caminhos dos arquivos finais, veredito da verificação e as lições novas adicionadas ao `rules.md`.
