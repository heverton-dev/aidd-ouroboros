import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { springPresets } from "../theme/physics";

export interface ConnectingLineProps {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  delayFrames?: number;
  color?: string;
  strokeWidth?: number;
}

export const ConnectingLine: React.FC<ConnectingLineProps> = ({
  x1,
  y1,
  x2,
  y2,
  delayFrames = 0,
  color = "#60A5FA",
  strokeWidth = 3,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const progress = spring({
    frame: Math.max(0, frame - delayFrames),
    fps,
    config: springPresets.smooth,
  });

  // Ponto de controle para curvatura suave estilo Bézier
  const dx = (x2 - x1) * 0.5;
  const cx1 = x1 + dx;
  const cy1 = y1;
  const cx2 = x2 - dx;
  const cy2 = y2;

  const pathData = `M ${x1} ${y1} C ${cx1} ${cy1}, ${cx2} ${cy2}, ${x2} ${y2}`;

  // Estimativa de comprimento para dashoffset
  const distance = Math.hypot(x2 - x1, y2 - y1) * 1.2;
  const strokeDashoffset = interpolate(progress, [0, 1], [distance, 0]);

  return (
    <svg
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        width: "100%",
        height: "100%",
        pointerEvents: "none",
        overflow: "visible",
      }}
    >
      <path
        d={pathData}
        fill="none"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeDasharray={distance}
        strokeDashoffset={strokeDashoffset}
        strokeLinecap="round"
      />
    </svg>
  );
};
