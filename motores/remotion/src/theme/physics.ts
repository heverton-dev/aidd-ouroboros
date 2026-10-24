/**
 * Presets de Física de Molas (Spring Physics) canônicos
 * Derivados por engenharia reversa do método de animação didática de Viktor Kav.
 */

export interface SpringConfig {
  damping: number;
  stiffness: number;
  mass: number;
  overshootClamping?: boolean;
}

export const springPresets: Record<"snappy" | "smooth" | "bouncy", SpringConfig> = {
  // Snappy: Ideal para cards conceituais, balões de código e pop-ins rápidos
  snappy: {
    damping: 12,
    stiffness: 120,
    mass: 0.6,
    overshootClamping: false,
  },
  // Smooth: Ideal para movimentos de câmera, transições de cena e drifts panorâmicos
  smooth: {
    damping: 20,
    stiffness: 80,
    mass: 1.2,
    overshootClamping: true,
  },
  // Bouncy: Ideal para ênfases pedagógicas, alertas, badges e efeitos lúdicos
  bouncy: {
    damping: 8,
    stiffness: 140,
    mass: 0.5,
    overshootClamping: false,
  },
};
