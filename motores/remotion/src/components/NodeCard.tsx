import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { springPresets } from "../theme/physics";

export interface NodeCardProps {
  title: string;
  description: string;
  x: number;
  y: number;
  delayFrames?: number;
  preset?: keyof typeof springPresets;
  icon?: string;
  borderColor?: string;
}

export const NodeCard: React.FC<NodeCardProps> = ({
  title,
  description,
  x,
  y,
  delayFrames = 0,
  preset = "snappy",
  icon,
  borderColor = "#3B82F6",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entrance = spring({
    frame: Math.max(0, frame - delayFrames),
    fps,
    config: springPresets[preset],
  });

  const scale = interpolate(entrance, [0, 1], [0.7, 1]);
  const opacity = interpolate(entrance, [0, 1], [0, 1]);

  return (
    <div
      style={{
        position: "absolute",
        left: x,
        top: y,
        transform: `scale(${scale})`,
        opacity,
        width: "280px",
        backgroundColor: "rgba(15, 23, 42, 0.95)",
        border: `2px solid ${borderColor}`,
        borderRadius: "12px",
        padding: "16px 20px",
        boxShadow: "0 10px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.5)",
        fontFamily: "Inter, sans-serif",
        backdropFilter: "blur(8px)",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
        {icon && <span style={{ fontSize: "20px" }}>{icon}</span>}
        <h3 style={{ margin: 0, fontSize: "18px", color: "#F8FAFC", fontWeight: 700 }}>{title}</h3>
      </div>
      <p style={{ margin: 0, fontSize: "14px", color: "#94A3B8", lineHeight: 1.4 }}>{description}</p>
    </div>
  );
};
