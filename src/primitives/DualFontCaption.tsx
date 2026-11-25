import React from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { COLORS, FONTS, ensureFontsLoaded } from '../styles/fonts';

export interface CaptionWordToken {
  text: string;
  bold?: boolean;
  accentColor?: string;
}

export interface DualFontCaptionProps {
  topWords?: string;
  keyword: string;
  bottomWords?: string;
  topPercent?: number;
  align?: 'left' | 'center' | 'right';
  theme?: 'light' | 'dark' | 'cobalt';
  keywordScalePx?: number;
  supportingScalePx?: number;
  accentColor?: string;
}

export const DualFontCaption: React.FC<DualFontCaptionProps> = ({
  topWords,
  keyword,
  bottomWords,
  topPercent = 68,
  align = 'center',
  theme = 'dark',
  keywordScalePx = 80,
  supportingScalePx = 38,
  accentColor,
}) => {
  ensureFontsLoaded();
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entrySpring = spring({
    frame,
    fps,
    config: {
      damping: 16,
      stiffness: 240,
      mass: 0.6,
    },
    durationInFrames: 12,
  });

  const scale = interpolate(entrySpring, [0, 1], [0.92, 1]);
  const translateY = interpolate(entrySpring, [0, 1], [18, 0]);
  const opacity = interpolate(frame, [0, 6], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const isLightCanvas = theme === 'light';
  const primaryTextColor = isLightCanvas ? COLORS.inkDark : COLORS.paperPure;
  const secondaryTextColor = isLightCanvas ? COLORS.inkMuted : 'rgba(245, 243, 238, 0.88)';
  const resolvedAccent =
    accentColor ?? (isLightCanvas ? COLORS.accentCobalt : COLORS.paperPure);

  return (
    <div
      style={{
        position: 'absolute',
        top: `${topPercent}%`,
        left: 80,
        right: 80,
        display: 'flex',
        flexDirection: 'column',
        alignItems:
          align === 'left' ? 'flex-start' : align === 'right' ? 'flex-end' : 'center',
        transform: `translateY(${translateY.toFixed(2)}px) scale(${scale.toFixed(4)})`,
        opacity,
        zIndex: 30,
        paddingTop: 20,
        paddingBottom: 20,
      }}
    >
      {topWords ? (
        <div
          style={{
            fontFamily: FONTS.sans,
            fontWeight: 500,
            fontSize: supportingScalePx,
            lineHeight: 1.35,
            color: secondaryTextColor,
            letterSpacing: '-0.01em',
            marginBottom: 4,
            textShadow: isLightCanvas
              ? 'none'
              : '0 4px 18px rgba(0, 0, 0, 0.65)',
          }}
        >
          {topWords}
        </div>
      ) : null}

      <div
        style={{
          fontFamily: FONTS.serifAccent,
          fontWeight: 700,
          fontStyle: 'italic',
          fontSize: keywordScalePx,
          lineHeight: 1.15,
          color: resolvedAccent,
          letterSpacing: '-0.02em',
          textAlign: align,
          textShadow: isLightCanvas
            ? '0 2px 10px rgba(30, 94, 255, 0.10)'
            : '0 6px 24px rgba(0, 0, 0, 0.75)',
        }}
      >
        {keyword}
      </div>

      {bottomWords ? (
        <div
          style={{
            fontFamily: FONTS.sans,
            fontWeight: 500,
            fontSize: supportingScalePx,
            lineHeight: 1.35,
            color: primaryTextColor,
            letterSpacing: '-0.01em',
            marginTop: 6,
            textShadow: isLightCanvas
              ? 'none'
              : '0 4px 18px rgba(0, 0, 0, 0.65)',
          }}
        >
          {bottomWords}
        </div>
      ) : null}
    </div>
  );
};
