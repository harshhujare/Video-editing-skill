import React from 'react';
import {
  AbsoluteFill,
  Easing,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

export type CameraTransitionType =
  | 'none'
  | 'zoom_through'
  | 'pan_left'
  | 'pan_up'
  | 'anchor_morph';

export interface CameraTransitionContract {
  type: CameraTransitionType;
  /** Transition duration in frames at 60fps (default: 18 frames = 300ms). */
  durationFrames?: number;
}

export interface CameraRigProps {
  x?: number;
  y?: number;
  scale?: number;
  rotate?: number;
  backgroundColor?: string;
  enterTransition?: CameraTransitionContract;
  exitTransition?: CameraTransitionContract;
  /** Optional explicit scene duration in frames; defaults to useVideoConfig().durationInFrames. */
  sceneDurationFrames?: number;
  children: React.ReactNode;
}

interface TransitionTransform {
  dx: number;
  dy: number;
  dScale: number;
  opacity: number;
  blurPx: number;
}

const DEFAULT_TRANSITION_FRAMES = 18;

function computeTransitionDelta(
  frame: number,
  totalFrames: number,
  enterTransition?: CameraTransitionContract,
  exitTransition?: CameraTransitionContract
): TransitionTransform {
  let dx = 0;
  let dy = 0;
  let dScale = 1;
  let opacity = 1;
  let blurPx = 0;

  if (enterTransition && enterTransition.type !== 'none') {
    const dur = Math.max(1, enterTransition.durationFrames ?? DEFAULT_TRANSITION_FRAMES);
    if (frame < dur) {
      const p = interpolate(frame, [0, dur], [0, 1], {
        easing: Easing.out(Easing.cubic),
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      });
      switch (enterTransition.type) {
        case 'zoom_through':
          dScale *= interpolate(p, [0, 1], [0.6, 1.0]);
          blurPx = Math.max(blurPx, interpolate(p, [0, 1], [8, 0]));
          opacity *= interpolate(frame, [0, Math.min(6, dur)], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });
          break;
        case 'pan_left':
          dx += interpolate(p, [0, 1], [1080, 0]);
          blurPx = Math.max(blurPx, interpolate(p, [0, 1], [6, 0]));
          break;
        case 'pan_up':
          dy += interpolate(p, [0, 1], [720, 0]);
          blurPx = Math.max(blurPx, interpolate(p, [0, 1], [6, 0]));
          break;
        case 'anchor_morph':
          dScale *= interpolate(p, [0, 1], [0.9, 1.0]);
          opacity *= interpolate(p, [0, 0.7], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });
          break;
      }
    }
  }

  if (exitTransition && exitTransition.type !== 'none' && totalFrames > 0) {
    const dur = Math.max(1, exitTransition.durationFrames ?? DEFAULT_TRANSITION_FRAMES);
    const exitStart = Math.max(0, totalFrames - dur);
    if (frame >= exitStart) {
      const p = interpolate(frame, [exitStart, totalFrames], [0, 1], {
        easing: Easing.in(Easing.cubic),
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      });
      switch (exitTransition.type) {
        case 'zoom_through':
          dScale *= interpolate(p, [0, 1], [1.0, 1.8]);
          blurPx = Math.max(blurPx, interpolate(p, [0, 1], [0, 10]));
          break;
        case 'pan_left':
          dx += interpolate(p, [0, 1], [0, -1080]);
          blurPx = Math.max(blurPx, interpolate(p, [0, 1], [0, 6]));
          break;
        case 'pan_up':
          dy += interpolate(p, [0, 1], [0, -720]);
          blurPx = Math.max(blurPx, interpolate(p, [0, 1], [0, 6]));
          break;
        case 'anchor_morph':
          dScale *= interpolate(p, [0, 1], [1.0, 1.1]);
          opacity *= interpolate(p, [0.3, 1], [1, 0], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });
          break;
      }
    }
  }

  return { dx, dy, dScale, opacity, blurPx };
}

/**
 * Shared virtual camera container. Wraps artwork, captions, and <TextureOverlay />
 * so textures move organically with scene motion and cross-scene transition handshakes.
 */
export const CameraRig: React.FC<CameraRigProps> = ({
  x = 0,
  y = 0,
  scale = 1,
  rotate = 0,
  backgroundColor = 'transparent',
  enterTransition,
  exitTransition,
  sceneDurationFrames,
  children,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const hasTransition =
    (enterTransition && enterTransition.type !== 'none') ||
    (exitTransition && exitTransition.type !== 'none');

  const delta = hasTransition
    ? computeTransitionDelta(
        frame,
        sceneDurationFrames ?? durationInFrames,
        enterTransition,
        exitTransition
      )
    : { dx: 0, dy: 0, dScale: 1, opacity: 1, blurPx: 0 };

  const finalX = x + delta.dx;
  const finalY = y + delta.dy;
  const finalScale = scale * delta.dScale;

  return (
    <AbsoluteFill
      style={{
        backgroundColor,
        overflow: 'hidden',
      }}
    >
      <AbsoluteFill
        style={{
          transform: `translate3d(${finalX.toFixed(2)}px, ${finalY.toFixed(2)}px, 0) scale(${finalScale.toFixed(4)}) rotate(${rotate.toFixed(2)}deg)`,
          transformOrigin: '50% 50%',
          opacity: delta.opacity,
          filter: delta.blurPx > 0.05 ? `blur(${delta.blurPx.toFixed(2)}px)` : undefined,
          willChange: 'transform, opacity, filter',
        }}
      >
        {children}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
