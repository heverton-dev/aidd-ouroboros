# Metodologia Extraída: {{NOME_DO_TEMA_OU_METODO}}

Fontes Primárias (REA Evidence Ledger):

| ID do Vídeo | Título / Criador | Duração | Arquivos de Evidência | Verificação REA |
|---|---|---|---|---|
| `{{VIDEO_ID}}` | {{TITULO}} — {{CRIADOR}} | {{DURACAO}} | `transcript.tsv`, `frames/` | Validado |

---

## 1. Princípio Técnico & Arquitetura de Execução
> **Evidence IDs:** [EVD-{{ID}}-01], [EVD-{{ID}}-02]

- **Conceito Central:** [OBSERVADO/DERIVADO] Como o autor produz o vídeo (ex: código em React/Remotion, Three.js + shaders, animações HTML/GSAP).
- **Controle Determinístico de Tempo:** Como a animação é dirigida por frame ou parâmetro $t$ em vez de clock de sistema, viabilizando renderização sem perda de frames.
- **Eficiência e Custos:** Consumo estimado de tokens de LLM por minuto de animação e tempo de renderização em máquina local.

---

## 2. Anatomia dos Prompts (Engenharia Reversa de Prompts)
> **Evidence IDs:** [EVD-{{ID}}-03]

Decomposição em blocos dos prompts apresentados na tela ou explicados no áudio:

1. **Header Técnico:** Resolução, aspect ratio (16:9, 9:16), framerate, runtime e regras de determinismo.
2. **Estilo Visual e Universo Gráfico:** Materiais, cores, iluminação, shaders, estética visual (ex: glassmorphism, flat didático, sci-fi).
3. **Camada Gráfica e Tipografia:** Fontes recomendadas, cartões de UI, ícones SVG e safe zones.
4. **Cinemática e Câmera:** Física de molas (springs), curvas bézier (easing), movimentos de câmera e transições de cena.
5. **Roteiro Cronometrado por Cenas:** Especificação detalhada com ações visuais atômicas por timestamp.
6. **Critérios de Validação Visual:** Verificação de contraste, legibilidade e limites de viewport.

### Prompt Reconstituído (Verbatim)
```text
{{PROMPT_MESTRE_EXTRAIDO}}
```

---

## 3. Diretrizes de Storytelling e Direção Didática
> **Evidence IDs:** [EVD-{{ID}}-04]

- Técnicas para traduzir conceitos abstratos em representações visuais concretas.
- Pacing e retenção (frequência de novos estímulos visuais a cada $X$ segundos).
- Metáforas visuais recorrentes (tubos conectores, nós orbitais, expansões de cards).
- Integração de áudio e locução (TTS, alinhamento fonético ou cortes manuais).

---

## 4. Esteira Operacional Passo a Passo
> **Evidence IDs:** [EVD-{{ID}}-05]

Sequência cronológica da linha de produção:
1. **Passo 1:** Concepção da explicação e roteiro textual.
2. **Passo 2:** Estruturação de cenas e storyboard descritivo.
3. **Passo 3:** Invocação do agente de código com o prompt da cena.
4. **Passo 4:** Preview e ajuste iterativo no estúdio interativo.
5. **Passo 5:** Export e composição com a locução final.

---

## 5. Lacunas e Omissões [DESCONHECIDOS REA]

Registro formal de detalhes técnicos omitidos no vídeo:
- *Lacuna 1:* {{PONTO_OMITIDO}}
- *Hipótese de Engenharia:* {{SOLUCAO_PROPOSTA}}
