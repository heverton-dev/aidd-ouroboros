# 04 — Tokens de Física e Animação

## 1. Por que Animações Amadoras Parecem Robóticas
A diferença primária entre um tutorial amador e um ensaio premium (Viktor Kav / Vox) reside no tratamento da curva de aceleração:
- **Amador:** Animação linear ($t$) ou ease genérico sem inércia.
- **Premium:** *Spring Physics* com inércia, massa e amortecimento calculados, ou curvas cúbicas de Bezier acentuadas.

## 2. Modelagem Matemática de Molas (Springs)
Em engines como Remotion (`spring({ frame, fps, config })`) ou bibliotecas CSS/JS:
- **`stiffness` (Rigidez):** Determina a velocidade inicial da aceleração. Valores ideais: 80 a 120.
- **`damping` (Amortecimento):** Controla a absorção do impacto no fim do curso. Valores baixos (<12) geram bounce (didático/lúdico); valores moderados (15 a 20) geram sensação de precisão corporativa (SaaS).
- **`mass` (Massa):** Simula o peso do objeto na tela. Cards pesados usam massa maior (1.2 a 1.8); tooltips e cursores usam massa leve (0.3 a 0.5).
