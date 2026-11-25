import React from 'react';
import {
  AbsoluteFill,
  Easing,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import { FONTS, ensureFontsLoaded } from '../styles/fonts';

export interface KineticWordSpec {
  text: string;
  revealFrame: number; // local frame within the scene/sequence when word triggers
  accent?: boolean; // true -> #FF1E1E bold large crimson keyword
  sizePx?: number;
  colorOverride?: string;
}

export interface KineticLineSpec {
  words: KineticWordSpec[];
  marginBottom?: number;
}

export interface KineticWordGroupProps {
  lines: KineticLineSpec[];
  theme?: 'cream' | 'dark' | 'aroll';
  topPercent?: number;
  leftPx?: number;
  rightPx?: number;
  align?: 'center' | 'left' | 'right';
  ghostEcho?: boolean;
  tiltDegrees?: number;
  tiltStartFrame?: number;
  backdropPill?: boolean;
}

export const KLICKPIN_COLORS = {
  creamBg: '#FAF6EE',
  darkBg: '#050507',
  inkBlack: '#111114',
  inkGrey: '#4A4946',
  crimsonRed: '#F51B1B',
  crimsonGlow: 'rgba(255, 28, 28, 0.82)',
  sCurveGrey: '#B9B6AF',
  cardGrey: '#8A8A8C',
};

export const KineticWordGroup: React.FC<KineticWordGroupProps> = ({
  lines,
  theme = 'cream',
  topPercent = 44,
  leftPx = 70,
  rightPx = 70,
  align = 'center',
  ghostEcho = false,
  tiltDegrees = 0,
  tiltStartFrame = 0,
  backdropPill = false,
}) => {
  ensureFontsLoaded();
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const isDark = theme === 'dark' || theme === 'aroll';

  const currentTilt =
    tiltDegrees !== 0
      ? interpolate(
          frame,
          [tiltStartFrame, tiltStartFrame + 14],
          [0, tiltDegrees],
          {
            easing: Easing.out(Easing.cubic),
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          }
        )
      : 0;

  const renderLines = (isGhost: boolean) =>
    lines.map((line, lineIdx) => (
      <div
        key={lineIdx}
        style={{
          display: 'flex',
          flexDirection: 'row',
          flexWrap: 'wrap',
          justifyContent:
            align === 'left'
              ? 'flex-start'
              : align === 'right'
              ? 'flex-end'
              : 'center',
          alignItems: 'baseline',
          gap: '14px',
          marginBottom: line.marginBottom ?? -4,
        }}
      >
        {line.words.map((w, wordIdx) => {
          const localF = frame - w.revealFrame;
          if (localF < -1) {
            return (
              <span
                key={wordIdx}
                style={{
                  opacity: 0,
                  fontFamily: FONTS.sans,
                  fontWeight: w.accent ? 800 : 500,
                  fontSize: w.sizePx ?? (w.accent ? 92 : 52),
                  lineHeight: 0.96,
                  letterSpacing: w.accent ? '-0.045em' : '-0.03em',
                }}
              >
                {w.text}
              </span>
            );
          }

          const sp = spring({
            frame: Math.max(0, localF),
            fps,
            config: {
              damping: 15,
              stiffness: 260,
              mass: 0.55,
            },
            durationInFrames: 14,
          });

          const opacity = interpolate(localF, [0, 3, 10], [0, 0.48, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });

          const blurPx = interpolate(localF, [0, 11], [11, 0], {
            easing: Easing.out(Easing.quad),
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });

          const translateY = interpolate(sp, [0, 1], [20, 0]);
          const scale = interpolate(sp, [0, 1], [0.88, 1]);

          const fontSize = w.sizePx ?? (w.accent ? 92 : 52);
          const color =
            w.colorOverride ??
            (w.accent
              ? KLICKPIN_COLORS.crimsonRed
              : isDark
              ? '#FFFFFF'
              : KLICKPIN_COLORS.inkBlack);

          const textShadow = w.accent
            ? isDark
              ? '0 0 26px rgba(255, 28, 28, 0.82), 0 0 58px rgba(255, 20, 20, 0.42)'
              : '0 4px 18px rgba(245, 27, 27, 0.18)'
            : isDark
            ? '0 0 18px rgba(255, 255, 255, 0.48), 0 4px 16px rgba(0, 0, 0, 0.85)'
            : 'none';

          return (
            <span
              key={wordIdx}
              style={{
                display: 'inline-block',
                fontFamily: FONTS.sans,
                fontWeight: w.accent ? 800 : 500,
                fontSize,
                lineHeight: 0.96,
                letterSpacing: w.accent ? '-0.045em' : '-0.03em',
                color,
                opacity: isGhost ? opacity * 0.11 : opacity,
                filter: `blur(${(isGhost ? blurPx + 2.5 : blurPx).toFixed(2)}px)`,
                transform: `translate3d(0, ${translateY.toFixed(2)}px, 0) scale(${scale.toFixed(4)})`,
                textShadow,
                willChange: 'transform, opacity, filter',
              }}
            >
              {w.text}
            </span>
          );
        })}
      </div>
    ));

  return (
    <div
      style={{
        position: 'absolute',
        top: `${topPercent}%`,
        left: leftPx,
        right: rightPx,
        display: 'flex',
        flexDirection: 'column',
        alignItems:
          align === 'left'
            ? 'flex-start'
            : align === 'right'
            ? 'flex-end'
            : 'center',
        transform: `rotate(${currentTilt.toFixed(2)}deg)`,
        zIndex: 35,
      }}
    >
      {ghostEcho ? (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            transform: 'translate3d(-28px, -6px, 0) scale(1.22)',
            pointerEvents: 'none',
            display: 'flex',
            flexDirection: 'column',
            alignItems:
              align === 'left'
                ? 'flex-start'
                : align === 'right'
                ? 'flex-end'
                : 'center',
          }}
        >
          {renderLines(true)}
        </div>
      ) : null}

      <div
        style={
          backdropPill
            ? {
                backgroundColor: 'rgba(5, 5, 7, 0.76)',
                backdropFilter: 'blur(12px)',
                padding: '24px 38px 28px 38px',
                borderRadius: 24,
                border: '1px solid rgba(255, 255, 255, 0.12)',
                boxShadow: '0 20px 50px rgba(0, 0, 0, 0.55)',
              }
            : undefined
        }
      >
        {renderLines(false)}
      </div>
    </div>
  );
};

export interface KlickpinGridProps {
  centerX?: number;
  centerY?: number;
  cols?: number;
  rows?: number;
  cellSize?: number;
  dark?: boolean;
  perspective3D?: boolean;
}

export const KlickpinDotGrid: React.FC<KlickpinGridProps> = ({
  centerX = 540,
  centerY = 920,
  cols = 8,
  rows = 8,
  cellSize = 54,
  dark = false,
  perspective3D = false,
}) => {
  const width = cols * cellSize;
  const height = rows * cellSize;
  const left = centerX - width / 2;
  const top = centerY - height / 2;

  const lineColor = dark ? 'rgba(255, 255, 255, 0.09)' : 'rgba(17, 17, 20, 0.08)';
  const dotColor = dark ? 'rgba(255, 255, 255, 0.28)' : 'rgba(17, 17, 20, 0.26)';

  return (
    <div
      style={{
        position: 'absolute',
        left,
        top,
        width,
        height,
        transform: perspective3D
          ? 'perspective(700px) rotateX(48deg) rotateZ(-18deg)'
          : undefined,
        pointerEvents: 'none',
        zIndex: 4,
      }}
    >
      <svg width={width} height={height} style={{ overflow: 'visible' }}>
        {Array.from({ length: cols + 1 }).map((_, c) => (
          <line
            key={`v-${c}`}
            x1={c * cellSize}
            y1={0}
            x2={c * cellSize}
            y2={height}
            stroke={lineColor}
            strokeWidth={1}
          />
        ))}
        {Array.from({ length: rows + 1 }).map((_, r) => (
          <line
            key={`h-${r}`}
            x1={0}
            y1={r * cellSize}
            x2={width}
            y2={r * cellSize}
            stroke={lineColor}
            strokeWidth={1}
          />
        ))}
        {Array.from({ length: cols + 1 }).map((_, c) =>
          Array.from({ length: rows + 1 }).map((__, r) => (
            <circle
              key={`d-${c}-${r}`}
              cx={c * cellSize}
              cy={r * cellSize}
              r={2.4}
              fill={dotColor}
            />
          ))
        )}
      </svg>
    </div>
  );
};

export const KlickpinEditorialStamps: React.FC<{
  showBarcode?: boolean;
  showHdSpec?: boolean;
  hdTop?: number;
}> = ({ showBarcode = true, showHdSpec = true, hdTop = 1480 }) => {
  const barWidths = [4, 2, 6, 2, 3, 5, 2, 2, 6, 3, 2, 4, 6, 2, 3, 5, 2, 4, 2, 5];
  let cursor = 0;

  return (
    <AbsoluteFill style={{ pointerEvents: 'none', zIndex: 25 }}>
      {showBarcode ? (
        <div
          style={{
            position: 'absolute',
            top: 240,
            right: 170,
            opacity: 0.85,
          }}
        >
          <svg width={132} height={54} viewBox="0 0 132 54">
            {barWidths.map((w, idx) => {
              const x = cursor;
              cursor += w + 2.5;
              return (
                <rect
                  key={idx}
                  x={x}
                  y={0}
                  width={w}
                  height={54}
                  fill="#151518"
                />
              );
            })}
          </svg>
        </div>
      ) : null}

      {showHdSpec ? (
        <div
          style={{
            position: 'absolute',
            top: hdTop,
            left: '50%',
            transform: 'translateX(-50%)',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            opacity: 0.72,
            fontFamily: FONTS.sans,
          }}
        >
          <div
            style={{
              width: 18,
              height: 18,
              borderRadius: 9,
              border: '2px solid #151518',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 9,
              fontWeight: 800,
            }}
          >
            +
          </div>
          <div
            style={{
              backgroundColor: '#151518',
              color: '#FAF6EE',
              fontSize: 11,
              fontWeight: 800,
              padding: '2px 6px',
              borderRadius: 3,
              letterSpacing: '0.04em',
            }}
          >
            HD
          </div>
          <div
            style={{
              fontSize: 8.5,
              fontWeight: 600,
              color: '#151518',
              lineHeight: 1.1,
              letterSpacing: '0.06em',
              textTransform: 'uppercase',
            }}
          >
            PUNE TECHIE SERIES // 60FPS
            <br />
            CTRL + ALT + PUNE ARCHIVE
          </div>
          <div
            style={{
              border: '1.5px solid #151518',
              borderRadius: 10,
              padding: '1px 6px',
              fontSize: 10,
              fontWeight: 800,
              color: '#151518',
            }}
          >
            4K
          </div>
        </div>
      ) : null}
    </AbsoluteFill>
  );
};

export const KlickpinSCurveRibbon: React.FC<{
  progress: number;
  strokeColor?: string;
  strokeWidth?: number;
}> = ({
  progress,
  strokeColor = KLICKPIN_COLORS.sCurveGrey,
  strokeWidth = 56,
}) => {
  const pathLength = 2400;
  const clamped = Math.max(0, Math.min(1, progress));
  const offset = pathLength * (1 - clamped);

  return (
    <svg
      width={1080}
      height={1920}
      viewBox="0 0 1080 1920"
      style={{
        position: 'absolute',
        inset: 0,
        pointerEvents: 'none',
        zIndex: 3,
      }}
    >
      <path
        d="M 180 -60 C 520 340, 490 880, 560 1120 C 630 1360, 760 1680, 1020 1980"
        fill="none"
        stroke={strokeColor}
        strokeWidth={strokeWidth}
        strokeLinecap="butt"
        strokeDasharray={pathLength}
        strokeDashoffset={offset}
      />
    </svg>
  );
};
