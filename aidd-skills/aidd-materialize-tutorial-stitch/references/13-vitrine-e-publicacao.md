# 13 — Vitrine da empresa e publicação (vários aplicativos, um endereço)

Uma empresa tem vários aplicativos (ex.: Cadastros, Hub de Materiais, Linktree). Cada um continua com sua pasta e seu
`catalogo.json` (ver `11-catalogo.md`); a **empresa** junta todos numa vitrine estilo streaming só, com um endereço.

```text
<empresa>/                      ex.: tutoriais-conexao/
├── empresa.json                fonte da verdade: nome, marca, aplicativos, vitrine, publicação
├── marca/                      logo.webp, simbolo.png, fontes.css, fonts/, design-tokens.json (uma marca para todos)
├── site/                       GERADO por `tutorial.py vitrine` (não versionar, não editar)
│   ├── index.html              página única: início com uma linha por aplicativo; #/<app> com as jornadas do app
│   ├── manifest.json           sha256 de cada arquivo + versão (é o que a publicação compara)
│   ├── assets/marca/…
│   └── apps/<app>/videos|capas|previas/NN-<slug>.*
├── .vitrine-cache.json         o que já foi gerado (assinatura da fonte + parâmetros)
└── .publicado.json             a última versão enviada
```

## 1. Tudo aqui é script (zero token)

| Etapa | Quem faz | Determinístico? |
|---|---|---|
| status de cada tutorial (render final no disco = gerado) | `catalog_refresh` | sim |
| vídeo para a web (faststart, sem recodificar) | ffmpeg `-c copy` | sim |
| capa e destaque (quadro a 40% do vídeo sem legenda; `capa_s` no catálogo muda o instante) | ffmpeg | sim |
| prévia do hover (8 s a partir de 25%; `previa_s` muda o início) | ffmpeg | sim |
| cores e fontes da página (design tokens; `cores` no `empresa.json` sobrescreve) | `vitrine_css` | sim |
| "Novo" (render até 14 dias antes do mais recente do app), "Atualizado em" (data do render mais recente) | dados do disco | sim |
| página (template `templates/vitrine.html` + JSON) | `vitrine_build` | sim |
| envio (só o que o `manifest.json` do servidor não tem; página por último; apaga o que saiu) | `vitrine_publish` | sim |
| conferência (baixa `https://<dominio>/manifest.json` e compara a versão) | `vitrine_publish` | sim |

Rodar de novo sem mudança nos vídeos não muda nenhum byte e não envia nada. O agente só **traduz o pedido em um comando**.

## 2. Pedido do usuário → comando (não interprete além disto)

| Pedido (qualquer forma parecida) | Comando |
|---|---|
| "cria a vitrine da empresa X", "quero um Netflix dos tutoriais da X" | `tutorial.py empresa init <empresa> --nome "X"` e copiar a marca para `<empresa>/marca/` |
| "põe o app Y na vitrine", "adiciona o Hub de Materiais" | `tutorial.py empresa add-app <empresa> --pasta <pasta-do-app> [--nome "Y"] [--slug y]` |
| "tira o app Y da vitrine" | `tutorial.py empresa remove-app <empresa> --slug y` |
| "quais apps estão na vitrine?", "como está a vitrine?" | `tutorial.py empresa list <empresa>` |
| "atualiza a vitrine", "monta a vitrine" (local) | `tutorial.py vitrine <empresa>` |
| "publica", "manda para o ar", "atualiza os tutoriais no site" | `tutorial.py publicar <empresa>` |
| "o que vai subir?", "simula a publicação" | `tutorial.py publicar <empresa> --dry-run` |
| "publica sozinho", "sempre que sair tutorial, já põe no ar", "publicação automática" | `tutorial.py publicar <empresa> --auto on` |
| "para de publicar sozinho", "eu publico na mão" | `tutorial.py publicar <empresa> --auto off` |
| "limpa o servidor", primeira publicação num servidor com arquivos antigos | `tutorial.py publicar <empresa> --dry-run --limpar`, mostrar a lista, e só com o ok: `--limpar` |
| "muda a contagem do próximo vídeo para N s" / "desliga o próximo automático" | `empresa.json > vitrine.proximo_s = N` (0 desliga) e `tutorial.py vitrine <empresa>` |

Gate de envio: publicar é ação externa. Com `publicacao.automatica = false`, pergunte antes de rodar `publicar`
(o `--dry-run` não precisa). Com `--auto on` o usuário já autorizou: cada `catalog render` de um app da empresa refaz a
vitrine e envia, sem perguntar.

## 3. Publicação automática (como funciona)

1. `empresa add-app` grava no `catalogo.json` do app o campo `"empresa": "<caminho relativo>"`.
2. Todo `tutorial.py catalog render <app>` (que a skill já roda ao fim de cada tutorial) refaz `site/` da empresa.
3. Se `empresa.json > publicacao.automatica` for `true`, envia em seguida. Falha de rede vira aviso; o catálogo não quebra.
4. O ssh roda com `BatchMode=yes`: sem chave aceita ele falha na hora, nunca fica esperando senha.

`publicacao` no `empresa.json`: `ssh` (alias do `~/.ssh/config`), `pasta_vps` (a pasta que o nginx serve), `dominio`
(para a conferência) e `automatica`. Nenhuma senha passa por aqui.

## 4. A página

- Um aplicativo só: igual à vitrine de produto (linhas por jornada no topo).
- Vários: menu com Início + um item por aplicativo; o início tem uma linha por aplicativo ("Ver tudo ›"); `#/<app>` mostra
  as jornadas do app; `#/<app>/<slug>` abre o tutorial direto (link para mandar a alguém).
- Busca em todos os aplicativos; "Continuar assistindo" e progresso ficam no navegador da pessoa.
- Só entra o que está pronto: com vários idiomas configurados (padrão), um tutorial com vídeo mas sem `idiomas/idiomas.json` fica como "em breve" — nada vai ao ar pela metade no meio da produção.
- Tela cheia é sempre a do player inteiro (`#pstage`: vídeo + legenda + botões): botão no topo, tecla F, duplo clique ou o botão nativo do vídeo (a página troca na hora). O navegador recusa tela cheia de `<dialog>` modal e a do `<video>` sozinho esconde a legenda. Na tela cheia nativa do iPhone e no picture-in-picture entra a faixa de legenda do próprio navegador, no mesmo idioma.
- Fim do vídeo: tela "A seguir" sobre o player escurecido, com a miniatura grande do próximo (mesma jornada do mesmo
  app, depois o próximo do app), anel de contagem regressiva sobre ela, "Começa em N s", "Assistir agora" e "Cancelar"
  (Esc também cancela, sem fechar o player). Último vídeo do app: tela "Você concluiu" com "Assistir de novo" e
  "Voltar aos tutoriais". `vitrine.proximo_s` muda o tempo (padrão 5); `0` só sugere, sem contagem.
