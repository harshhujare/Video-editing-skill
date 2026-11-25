import React from 'react';
import { AbsoluteFill, Img } from 'remotion';

export interface TextureOverlayProps {
  src: string;
  opacity?: number;
  blendMode?: React.CSSProperties['mixBlendMode'];
  mode?: React.CSSProperties['mixBlendMode'];
}

export const TextureOverlay: React.FC<TextureOverlayProps> = ({
  src,
  opacity = 0.18,
  blendMode,
  mode,
}) => {
  const clampedOpacity = Math.max(0.12, Math.min(0.22, opacity));
  const resolvedBlendMode = mode ?? blendMode ?? 'multiply';
  return (
    <AbsoluteFill
      style={{
        pointerEvents: 'none',
        zIndex: 50,
        opacity: clampedOpacity,
        mixBlendMode: resolvedBlendMode,
      }}
    >
      <Img
        src={src}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
        }}
      />
    </AbsoluteFill>
  );
};
