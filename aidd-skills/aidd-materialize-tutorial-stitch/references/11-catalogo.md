# 11 — Modo catálogo (todos os tutoriais de um produto)

Quando o usuário pede "os tutoriais da minha aplicação" (não um fluxo só), a skill analisa o produto inteiro, propõe um **menu de tutoriais** e passa a gerenciá-lo. Tudo fica numa pasta do produto em kebab-case (ex.: `cadastros-conexao/`).

```text
<produto>/
├── CATALOGO.md        menu legível (gerado; não editar à mão)
├── catalogo.json      fonte da verdade: produto, perfis, achados, tutoriais, padrões
├── mapa-do-app/       capturas da análise (por perfil: telas, controles, screenshots)
├── compartilhado/     design-tokens.json, brand/ (marca única para todos os tutoriais)
└── <tutorial>/        um projeto de tutorial completo por item (estrutura do T0)
```

## 1. Análise (pedido: "catalogo <url>" ou "quero os tutoriais de <url>")

1. **Reconhecimento passivo** da URL (REA `capture_browser_scenario` só com espera): há login? atalhos de teste? quais perfis?
2. **Autorização de entrada** (gate): atalhos de teste da própria tela, sessão do navegador do usuário (`--entrar cdp`) ou só páginas públicas. Nunca digitar senha.
3. **Mapeamento por perfil**:
   ```bash
   python HOME/scripts/explore.py <produto>/mapa-do-app/perfis --base <url> --perfil "<Perfil>" --entrar atalho
   python HOME/scripts/explore.py <produto>/mapa-do-app/perfis --base <url> --perfil "<Perfil>" --entrar cdp --cdp http://127.0.0.1:9222 --target <id>
   python HOME/scripts/explore.py <produto>/mapa-do-app/perfis --base <url> --perfil "<Página>" --entrar publico --caminho /rota
   ```
   - Passada 1: entra e lê a tela inicial (screenshot, árvore de acessibilidade, controles).
   - Passada 2: clica **só** em controles da lista de permitidos (visualização, filtro, aba, ordenação, paginação) e abre links internos seguros por endereço. Ações (salvar, enviar, gerar, criar, excluir, inativar, exportar, imprimir, sair…) são **listadas sem clicar** em `acoes_nao_executadas`.
   - Ordem anti-bloqueio: filtros → abas → Próxima → Anterior (o REA interrompe o cenário no primeiro clique que falha).
4. **Design system** uma vez para o produto: `hyperframes capture` + `tutorial.py design-tokens … --out <produto>/compartilhado`.
5. **Classificação** (agente): cada tela vira jornadas; cada jornada vira um tutorial com `slug`, `titulo`, `perfil`, `jornada`, `objetivo`, `telas`, `duracao_s`, `prioridade` (1 a 3), `tipo` (`observacao` ou `acao`), `requer` (o que precisa de autorização) e `status`. Registre também `achados` (defeitos vistos, dados pessoais na tela, telas indisponíveis).
6. `python HOME/scripts/tutorial.py catalog render <produto>` → `CATALOGO.md` com menu por jornada, status, saídas já geradas e o comando de cada item.

Gate **C1**: o usuário revisa o catálogo (pode remover, reordenar, adicionar) antes de gerar.

## 2. Comandos do usuário e o que a skill faz

| Pedido | Ação |
|---|---|
| `gerar <slug>` | `tutorial.py init <produto>/<pasta>` com os `padroes` do catálogo → `capture --roteiro` → o agente escreve `spec.json` → `tutorial.py produzir <pasta>` → traduções se pedir → `catalog render` |
| `gerar todos` | laço: `tutorial.py catalog next <produto>` → `gerar` o item → próximo, **um tutorial por sessão (ou compactação) entre itens**. Itens `tipo: acao` param no gate pedindo a autorização descrita em `requer`. Retomável: o status fica no `catalogo.json` |
| `regenerar <slug>` | refaz o item (iteração travada se for ajuste; do zero se a tela mudou) |
| `adicionar "<fluxo>"` | captura o fluxo, `tutorial.py catalog add <produto> --titulo … --perfil … --objetivo …`, `catalog render` |
| `remover <slug>` | `tutorial.py catalog remove <produto> --slug <slug>` (a pasta não é apagada) |
| `refazer catalogo` | repete a análise, compara com o mapa anterior e marca `desatualizado` os tutoriais cujas telas mudaram (`catalog set --status desatualizado`) |
| `adequar <slug> …` / `mudar legenda <slug> …` | ver `12-saidas.md` |

## 3. Regras

- **Só observação na análise.** Nenhum formulário preenchido, nenhuma ação que grave dados. O que exige ação vira item `tipo: acao` com `requer`.
- **Dados pessoais** vistos no mapeamento ficam só no `mapa-do-app/` local; nos vídeos, sempre fictícios.
- **Uma marca por produto**: todos os itens usam `compartilhado/brand/brand.css` e passam no `audit brand`.
- **Padrões do produto** (`catalogo.json` > `padroes`: canais, formatos, resoluções, legenda) valem para todo item novo; o usuário pode sobrescrever por item.
- **Status** é recalculado do disco a cada `catalog render` (render final presente = `gerado`); a pasta do tutorial é o campo `pasta` do item (relativo ao produto) ou `<produto>/<slug>`.
- **Vitrine**: se o produto faz parte de uma empresa (`"empresa"` no `catalogo.json`, gravado por `tutorial.py empresa add-app`), cada `catalog render` também refaz a vitrine da empresa e, com a publicação automática ligada, envia. Ver `13-vitrine-e-publicacao.md`.
