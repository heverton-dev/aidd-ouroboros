import React from "react";
import { AbsoluteFill } from "remotion";
import { ConnectingLine } from "./components/ConnectingLine";
import { NodeCard } from "./components/NodeCard";

export interface MainCompositionProps {
  title: string;
  subtitle: string;
}

export const MainComposition: React.FC<MainCompositionProps> = ({ title, subtitle }) => {
  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#0B0F19",
        fontFamily: "Inter, sans-serif",
        color: "#F8FAFC",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Cabeçalho */}
      <div style={{ position: "absolute", top: "60px", left: "80px" }}>
        <h1
          style={{
            fontSize: "44px",
            fontWeight: 800,
            margin: "0 0 10px 0",
            background: "linear-gradient(135deg, #60A5FA 0%, #A855F7 100%)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
          }}
        >
          {title}
        </h1>
        <p style={{ margin: 0, fontSize: "20px", color: "#94A3B8" }}>{subtitle}</p>
      </div>

      {/* Linhas conectando os nós do diagrama */}
      <ConnectingLine x1={420} y1={450} x2={680} y2={450} delayFrames={20} color="#3B82F6" />
      <ConnectingLine x1={960} y1={450} x2={1220} y2={450} delayFrames={40} color="#8B5CF6" />

      {/* Nós do diagrama (Pipeline Viktor Kav) */}
      <NodeCard
        x={140}
        y={380}
        delayFrames={5}
        preset="snappy"
        icon="🎙️"
        title="1. Áudio Whisper"
        description="Transcreve fala em TSV com marcas temporais exatas em ms."
        borderColor="#3B82F6"
      />

      <NodeCard
        x={680}
        y={380}
        delayFrames={25}
        preset="snappy"
        icon="📐"
        title="2. Remotion Spring"
        description="Anima cartões e nós usando física de molas determinística a 60 fps."
        borderColor="#8B5CF6"
      />

      <NodeCard
        x={1220}
        y={380}
        delayFrames={45}
        preset="bouncy"
        icon="🎬"
        title="3. Stitch FFmpeg"
        description="Concatena gravações reais de tela e animações conceituais no vídeo final."
        borderColor="#EC4899"
      />
    </AbsoluteFill>
  );
};
