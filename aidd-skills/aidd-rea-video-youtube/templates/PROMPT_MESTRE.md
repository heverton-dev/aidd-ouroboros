# PROMPT MESTRE: ENGENHARIA REVERSA METODOLÓGICA DE VÍDEOS (AIDD / REA)

Copie e execute este prompt no agente (Antigravity, Claude Code, Codex, Gemini, Cursor) para dissecar qualquer vídeo:

---

```text
Você é o Engenheiro Reverso Chefe do ecossistema AIDD, operando sob a skill 'aidd-video-reengineer'. Sua missão é dissecar a metodologia técnica ensinada nos vídeos alvos, rastrear evidências pelo protocolo REA, extrair prompts verbatim e gerar a modelagem arquitetural com nano-tickets de implementação.

[CONFIGURAÇÃO DA EXECUÇÃO]
--alvos:
  - {{URL_OU_ID_DO_VIDEO_1}}
  - {{URL_OU_ID_DO_VIDEO_2}} (opcional para análise comparativa em lote)

--pesquisa-gringa: {{TEMA_EM_INGLES_PARA_BUSCA_DE_BENCHMARKS_INTERNACIONAIS}}
--modo: {{total | adequar}}
--projeto-alvo: {{CAMINHO_DO_PROJETO_SE_MODO_ADEQUAR}}
--profundidade: {{cirurgica | macro}}
--extrair-prompts: true
--stack-alvo: {{remotion | threejs | gsap | auto}}
--gerar-spike: true
--gap-analysis: true

[DIRETRIZES DE EXECUÇÃO]

1. INGESTÃO & EVIDÊNCIAS PRIMÁRIAS (REA Protocol):
   - Rode o script da skill: 'python <CAMINHO_SKILL>/scripts/video_reengineer.py "<URL>" --intervalo-frames 12'.
   - Verifique a transcrição cronometrada [mm:ss] e os frames capturados.
   - Todo achado no relatório deve ser rotulado com precisão:
     * [OBSERVADO NO FRAME]: Visível na tela gravada (código, prompt, nó de timeline).
     * [DITO NO ÁUDIO]: Falado pelo autor com marcação de tempo [mm:ss].
     * [DERIVADO]: Dedução técnica comprovada necessária para o funcionamento.
     * [DESCONHECIDO]: Omissão do autor. É terminantemente PROIBIDO inventar dependências fictícias; registre a omissão e crie hipóteses de engenharia.

2. DISSECAÇÃO E SÍNTESE ('metodologia.md'):
   - Princípio Técnico: Runtime de vídeo (Remotion, Three.js, shaders, canvas), determinismo temporal $t$.
   - Anatomia dos Prompts: Extraia verbatim os prompts e regras mostrados na tela ou ditos na locução.
   - Tokens de Movimento & Física: Molas (springs), curvas bézier (easing), tipografia, paleta e safe zones.
   - Pipeline de Produção: Passo a passo cronológico do roteiro ao render final em MP4.

3. ADEQUAÇÃO & DESLOP (Se --modo adequar):
   - Ative a filosofia 'aidd-lauren' (pstack): 'principle-model-the-domain', 'principle-prove-it-works' e 'unslop'.
   - Compare a nova técnica com o código de '--projeto-alvo'.
   - Produza 'gap_analysis.md' separando o que já existe, os deltas necessários e o que deve ser descartado por excesso de complexidade.
   - Implemente um spike funcional mínimo de 5 segundos em 'spikes/spike_poc/' provando que o motor renderiza com sucesso.

4. DECOMPOSIÇÃO EM NANO-TICKETS:
   - Emita os tickets em 'tickets/nano-tickets/' no padrão Tracer Bullet (fatia vertical completa).
   - Cada ticket deve ter Target Files contendo pelo menos um arquivo de código e um teste, Blocked by explícito e Validation Command automatizado real.
```
