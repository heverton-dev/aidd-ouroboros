import React from "react";
import { Composition } from "remotion";
import { MainComposition } from "./Composition";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="Main"
        component={MainComposition}
        durationInFrames={300}
        fps={60}
        width={1920}
        height={1080}
        defaultProps={{
          title: "Tutorial Animado Viktor Kav Method",
          subtitle: "Pipelines Autônomos de Código e Animação",
        }}
      />
    </>
  );
};
