# Diretrizes de IA para o Motor Remotion (Viktor Kav Method)

## 1. Princípios de Animação Conceitual
1. **Determinação por Frame:** Nunca use `Math.random()` ou APIs não determinísticas de tempo. Use sempre `useCurrentFrame()` e `useVideoConfig()`.
2. **Física de Molas (`spring`):** Toda entrada e transição de nós em diagramas deve usar `spring()` do Remotion com configurações ajustadas:
   - **Snappy (Cards e Balões):** `damping: 12`, `stiffness: 120`, `mass: 0.6`
   - **Smooth (Câmera e Pan):** `damping: 20`, `stiffness: 80`, `mass: 1.2`
   - **Bouncy (Ênfase ou Alerta):** `damping: 8`, `stiffness: 140`, `mass: 0.5`
3. **Escala e Cores:**
   - Resolução padrão: 1920x1080 @ 60fps.
   - Paleta de fundo escuro com contraste técnico (#0B0F19).
   - Tipografia limpa sans-serif (Inter / JetBrains Mono para código).
4. **Isolamento de Cenas:** Cada conceito didático deve ser modelado como uma composição isolada ou `<Series.Sequence>`.
