# 05 — Gap Analysis e Filosofia `aidd-lauren` (*pstack*)

## 1. O Risco de "Inchaço por Novidade" (*Code Slop*)
Ao analisar uma metodologia sofisticada (ex: Three.js ou Remotion), o impulso comum é descartar o sistema existente e reescrever tudo do zero. A disciplina da Lauren Tan (`aidd-lauren` / *pstack*) impede essa armadilha:

* **`principle-model-the-domain`:** Mapeie os dados do projeto atual antes de escrever uma única linha do novo motor. O que entra no gerador? Roteiro, áudio, lista de cenas. Se o modelo de domínio já existe, o novo motor deve apenas consumir esse contrato.
* **`principle-prove-it-works`:** Nenhuma adequação é aceita sem a prova de um artefato real. O agente deve renderizar um vídeo teste de 5 segundos (`spikes/spike_poc/`) antes de qualquer alteração na base de código de produção.
* **`unslop`:** Identifique o que **NÃO** deve ser importado. Se o autor usa um software de edição pago (Final Cut, DaVinci) apenas para juntar áudio, isso não deve virar dependência do nosso projeto — usamos automação determinística via FFmpeg.
