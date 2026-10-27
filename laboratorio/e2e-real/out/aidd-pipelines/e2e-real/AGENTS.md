# AGENTS.md - Governanca para Agentes de IA

Diretrizes para agentes autonomos que executam, monitoram ou ajustam o pipeline e2e-real.

## 1. Regras Operacionais Inegociaveis
1. Nao modifique manualmente arquivos em `context/handoffs/`. As mutacoes devem ocorrer estritamente pelos runners e skills.
2. Em caso de falha, inspecione `state.json` para identificar o no exato e o erro reportado.
3. Respeite o isolamento canônico do pipeline. Nao polua a raiz do projeto.
4. Assegure a presenca do arquivo de entrada em `context/input/pipeline_input.json` antes do disparo.
