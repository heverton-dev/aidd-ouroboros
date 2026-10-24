# 01 — Protocolo REA de Evidências

## 1. Classificação Obrigatória de Fatos
No padrão REA (*Reverse Engineer Anything*), nenhuma afirmativa pode ser feita em `metodologia.md` sem um marcador epistêmico:

* **`[OBSERVADO NO FRAME]`**: Dado extraído diretamente de uma captura de tela de alta resolução (`frames/*.png`).
  * *Exemplo:* "Aos 03:45, a tela do terminal exibe o comando `npx remotion skills add` [OBSERVADO NO FRAME: `frames/frame_0225.png`]."
* **`[DITO NO ÁUDIO]`**: Frase dita pelo criador na faixa de áudio transcrita.
  * *Exemplo:* "O autor afirma que interpolações spring geram mais retenção que ease-in-out [DITO NO ÁUDIO: `transcript.tsv#L48 (04:12)`]."
* **`[DERIVADO]`**: Conclusão técnica necessária para a reprodução funcional.
  * *Exemplo:* "A animação opera a 60 fps determinísticos baseada no frame count do Remotion [DERIVADO]."
* **`[DESCONHECIDO REA]`**: Ponto de incerteza, corte no vídeo ou código ocultado.
  * *Exemplo:* "O vídeo não mostra o script de stitching de áudio final [DESCONHECIDO REA]. Solução de engenharia recomendada: usar ffmpeg concat demuxer."

## 2. Invariante Antialucinação
Se um agente de IA não conseguir localizar evidência visual ou de áudio para uma determinada afirmação, ele está terminantemente proibido de inventar código sob a alegação de que "o vídeo ensinou assim". O agente deve registrar a lacuna como `[DESCONHECIDO REA]`.
