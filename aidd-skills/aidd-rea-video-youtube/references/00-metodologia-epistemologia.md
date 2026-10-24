# 00 — Epistemologia da Engenharia Reversa de Vídeos

## 1. O Problema da Mídia em Vídeo como Caixa-Preta
Diferente de um repositório de código aberto onde todo o histórico de commits e árvores de arquivos estão expostos, o vídeo técnico do YouTube é um produto final renderizado. O criador de conteúdo filtra o processo, corta erros e exibe apenas trechos da sua esteira operacional.

O objetivo da Engenharia Reversa Metodológica é reconstruir a **causa** a partir do **efeito**:
- A partir dos frames de saída $\rightarrow$ inferir a arquitetura da cena, easing, materiais e viewport.
- A partir dos trechos visíveis de código/prompts $\rightarrow$ reconstruir a gramática dos prompts mestres.
- A partir do áudio e da locução $\rightarrow$ derivar as regras de direção de arte, ritmo e pacing.

## 2. As Três Fases Epistemológicas
1. **Fase de Observação Direta:** O que pode ser visto ou ouvido com precisão absoluta (evidência primária irrefutável).
2. **Fase de Derivação Mecânica:** Conclusões dedutivas obrigatórias (exemplo: se há reflexo dinâmico no 3D, uma fonte de luz pontual ou envmap foi instanciada).
3. **Fase de Formulação de Hipóteses:** Pontos em que o criador ocultou parâmetros ou ferramentas proprietárias. Aqui a IA gera soluções funcionais alternativas rotuladas explicitamente como hipótese.
