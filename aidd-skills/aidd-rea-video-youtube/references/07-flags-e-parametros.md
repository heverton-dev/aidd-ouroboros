# 07 — Flags e Parâmetros de Execução

## 1. Tabela Completa de Flags

| Flag | Tipo | Padrão | Descrição |
|---|---|---|---|
| `--alvos` | Lista de strings | Obrigatório | URLs ou IDs do YouTube a serem dissecados. |
| `--pesquisa-gringa` | String | Vazio | Query em inglês para localizar os 3 vídeos internacionais correlatos mais relevantes. |
| `--modo` | `total` \| `adequar` | `total` | `total`: modelagem isolada 1:1.<br>`adequar`: integração seletiva contra projeto alvo existente. |
| `--projeto-alvo` | Caminho | `./` | Caminho da base de código a ser atualizada. |
| `--profundidade` | `macro` \| `cirurgica` | `cirurgica` | Granularidade da extração de código e frames visuais. |
| `--extrair-prompts` | Booleana | `true` | Força a transcrição verbatim dos prompts exibidos nas telas dos vídeos. |
| `--stack-alvo` | `remotion` \| `threejs` \| `gsap` \| `auto` | `auto` | Direciona o modelo de scaffolding para a biblioteca desejada. |
| `--gerar-spike` | Booleana | `true` | Cria protótipo executável de 5 segundos provando a técnica no ambiente local. |
| `--gap-analysis` | Booleana | `true` | Produz `gap_analysis.md` com matriz comparativa e ROI técnico. |
