import React from 'react';
import {
  AbsoluteFill,
  Easing,
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import { FONTS, ensureFontsLoaded, splitMarathiAksharas } from '../styles/fonts';

export interface EditorialWord {
  text: string;
  /** Local frame within the scene when this word begins speaking. */
  startFrame: number;
  accent?: boolean;
  accentColor?: string;
}

export interface EditorialCaptionProps {
  words: EditorialWord[];
  theme?: 'dark' | 'light';
  /** Vertical position as % from top (default: 72% on dark footage, 76% on light paper). */
  topPercent?: number;
  fontSize?: number;
  maxWidth?: number;
  /** Soft natural dark film fade at the very bottom edge on dark footage (no opaque box). */
  bottomScrim?: boolean;
} 

/**
 * Splits a scene's word stream into 1 or 2 asymmetric kinetic lockup tiers
 * (matching Reference Video 1 seg_001 "Most Great / Inventions / come from / Labs."
 * and Klickpin kinetic dramatic scale contrast).
 */
function buildKineticTiers(words: EditorialWord[]): EditorialWord[][] {
  if (words.length <= 3) {
    return [words];
  }
  // Prefer splitting cleanly right before the main accent cluster or at midpoint
  const firstAccentIdx = words.findIndex((w, i) => i > 0 && w.accent);
  let splitAt =
    firstAccentIdx >= 1 && firstAccentIdx <= words.length - 1
      ? firstAccentIdx
      : Math.ceil(words.length / 2);
  if (splitAt > 4) {
    splitAt = Math.ceil(words.length / 2);
  }
  return [words.slice(0, splitAt), words.slice(splitAt)];
}

/**
 * True Kinetic Typography over documentary footage:
 * - Expressive Marathi display font contrast (Mukta SemiBold supporting vs Rozha One / Khand Bold 1.7x hero slams)
 * - Asymmetric 2-tier staggered editorial lockup (NOT a generic flat single-row subtitle)
 * - Spring overshoot scale slam (1.38 -> 1.0), directional motion-blur snap (16px -> 0px),
 *   active-word spotlight pulse, and luminous chromatic bloom on hero impacts.
 */
export const EditorialCaption: React.FC<EditorialCaptionProps> = ({
  words,
  theme = 'dark',
  topPercent = 73,
  fontSize = 46,
  maxWidth = 940,
  bottomScrim = true,
}) => {
  ensureFontsLoaded();
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const isDark = theme === 'dark';
  const baseColor = isDark ? '#F5F2EB' : '#16181C';
  const defaultAccent = isDark ? '#F6CF4E' : '#0D3494';

  const tiers = buildKineticTiers(words);
  const adjustedTop = tiers.length > 1 ? Math.max(66, topPercent - 5) : topPercent;

  // Find currently active word index for live kinetic spotlight
  let activeFlatIdx = -1;
  for (let i = 0; i < words.length; i++) {
    if (frame >= words[i].startFrame) {
      activeFlatIdx = i;
    }
  }

  // Subtle container kinetic breathe synced to active word shift
  const activeStart = activeFlatIdx >= 0 ? words[activeFlatIdx].startFrame : 0;
  const activeSince = Math.max(0, frame - activeStart);
  const containerTilt = interpolate(activeSince, [0, 14], [activeFlatIdx % 2 === 0 ? -1.1 : 0.9, 0], {
    easing: Easing.out(Easing.cubic),
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  let flatCursor = 0;

  return (
    <>
      {isDark && bottomScrim ? (
        <div
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            bottom: 0,
            height: 680,
            background:
              'linear-gradient(180deg, rgba(10,11,13,0) 0%, rgba(10,11,13,0.52) 50%, rgba(10,11,13,0.88) 100%)',
            pointerEvents: 'none',
            zIndex: 18,
          }}
        />
      ) : null}

      <div
        style={{
          position: 'absolute',
          top: `${adjustedTop}%`,
          left: '50%',
          transform: `translateX(-50%) rotate(${containerTilt.toFixed(2)}deg)`,
          width: maxWidth,
          paddingTop: 22,
          paddingBottom: 22,
          paddingLeft: 24,
          paddingRight: 24,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 0,
          zIndex: 24,
          pointerEvents: 'none',
        }}
      >
        {tiers.map((tier, tierIdx) => {
          const offsetX = tiers.length > 1 ? (tierIdx === 0 ? -24 : 20) : 0;
          return (
            <div
              key={tierIdx}
              style={{
                display: 'flex',
                flexWrap: 'wrap',
                justifyContent: 'center',
                alignItems: 'baseline',
                columnGap: 18,
                rowGap: 4,
                transform: `translate3d(${offsetX}px, 0, 0)`,
                marginTop: tierIdx === 1 ? -18 : 0,
              }}
            >
              {tier.map((w, wordIdx) => {
                const myFlatIdx = flatCursor++;
                const localF = frame - w.startFrame;
                if (localF < -1) {
                  return null;
                }

                const isAccent = Boolean(w.accent);
                const isActive = myFlatIdx === activeFlatIdx;
                const isPast = myFlatIdx < activeFlatIdx;

                const sp = spring({
                  frame: Math.max(0, localF),
                  fps,
                  config: isAccent
                    ? { damping: 12, stiffness: 280, mass: 0.55 }
                    : { damping: 16, stiffness: 240, mass: 0.6 },
                });

                const entryOpacity = interpolate(localF, [0, 5], [0, 1], {
                  extrapolateLeft: 'clamp',
                  extrapolateRight: 'clamp',
                });
                const finalOpacity = isPast && !isAccent ? entryOpacity * 0.78 : entryOpacity;

                const blurPx = interpolate(localF, [0, isAccent ? 10 : 7], [isAccent ? 16 : 9, 0], {
                  easing: Easing.out(Easing.quad),
                  extrapolateLeft: 'clamp',
                  extrapolateRight: 'clamp',
                });

                const entryScale = isAccent
                  ? interpolate(sp, [0, 1], [1.38, 1.0])
                  : interpolate(sp, [0, 1], [0.84, 1.0]);
                const activePulse = isActive ? 1.05 : 1.0;
                const finalScale = entryScale * activePulse;

                const dy = isAccent
                  ? interpolate(sp, [0, 1], [30, 0])
                  : interpolate(sp, [0, 1], [16, 0]);
                const dx = isAccent
                  ? interpolate(sp, [0, 1], [tierIdx === 0 ? -18 : 18, 0])
                  : 0;

                const color = isAccent ? (w.accentColor ?? defaultAccent) : baseColor;
                const wordFontSize = isAccent
                  ? Math.round(fontSize * 1.62)
                  : Math.round(fontSize * 0.94);

                // Impact bloom glow flashes bright on entry frames 0..10 then settles cleanly
                const bloomIntensity = interpolate(localF, [0, 5, 18], [0.95, 0.75, 0.38], {
                  extrapolateLeft: 'clamp',
                  extrapolateRight: 'clamp',
                });

                const textShadow = isDark
                  ? isAccent
                    ? `0 0 ${Math.round(34 * bloomIntensity)}px ${color}, 0 6px 26px rgba(0,0,0,0.92)`
                    : '0 4px 18px rgba(0,0,0,0.88)'
                  : isAccent
                  ? `0 4px 18px rgba(0,0,0,0.12)`
                  : 'none';

                // Alternate Rozha One (high-contrast Didone serif) & Khand Bold (condensed kinetic poster)
                // Digits/₹ get Khand Bold for crisp tabular numerals; Marathi emphasis gets Rozha One / Khand
                const hasDigits = /[0-9₹%]/.test(w.text);
                const fontFamily = isAccent
                  ? hasDigits
                    ? FONTS.displayKinetic
                    : FONTS.displaySerif
                  : FONTS.bodyMarathi;

                return (
                  <span
                    key={`${wordIdx}-${w.text}`}
                    style={{
                      display: 'inline-block',
                      fontFamily,
                      fontWeight: isAccent ? (hasDigits ? 900 : 700) : 600,
                      fontSize: wordFontSize,
                      lineHeight: 1.48,
                      letterSpacing: isAccent && hasDigits ? '-0.01em' : '0.01em',
                      color,
                      opacity: finalOpacity,
                      filter: blurPx > 0.15 ? `blur(${blurPx.toFixed(2)}px)` : undefined,
                      transform: `translate3d(${dx.toFixed(1)}px, ${dy.toFixed(1)}px, 0) scale(${finalScale.toFixed(4)})`,
                      textShadow,
                      fontVariantNumeric: 'tabular-nums',
                      willChange: 'transform, opacity, filter',
                    }}
                  >
                    {w.text}
                  </span>
                );
              })}
            </div>
          );
        })}
      </div>
    </>
  );
};

export interface PaperBreatherProps {
  words: EditorialWord[];
  subLabel?: string;
  subLabelFrame?: number;
  backgroundColor?: string;
  fontSize?: number;
}

/**
 * Spatial Diagonal Kinetic Paper Breather:
 * Directly modeled on Reference Video 1's "There / has / to / be / a / better / way"
 * & "And / the / strangest / part" — words land sequentially along an editorial diagonal
 * with dramatic Rozha One / Khand scale contrast, subtle tilt, motion-blur snap, and
 * a gentle virtual camera drift tracking the spoken rhythm.
 */
export const PaperBreatherContent: React.FC<PaperBreatherProps> = ({
  words,
  subLabel,
  subLabelFrame = 45,
  backgroundColor = '#D9DAD7',
  fontSize = 62,
}) => {
  ensureFontsLoaded();
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Gentle camera drift following the diagonal word progression
  const panY = interpolate(frame, [0, 175], [34, -38], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const panX = interpolate(frame, [0, 175], [22, -22], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Active word index for depth-of-field fade on older words
  let activeIdx = 0;
  for (let i = 0; i < words.length; i++) {
    if (frame >= words[i].startFrame) {
      activeIdx = i;
    }
  }

  // Build organic diagonal staircase coordinates across the 1080x1920 paper canvas
  const count = Math.max(1, words.length);
  const subOpacity = interpolate(frame, [subLabelFrame, subLabelFrame + 16], [0, 0.78], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor,
        overflow: 'hidden',
      }}
    >
      {/* Subtle photographic paper radial vignette + diagonal shadow */}
      <AbsoluteFill
        style={{
          background:
            'radial-gradient(ellipse at 50% 48%, rgba(255,255,255,0.22) 0%, rgba(0,0,0,0.0) 56%, rgba(0,0,0,0.20) 100%)',
          pointerEvents: 'none',
        }}
      />

      <AbsoluteFill
        style={{
          transform: `translate3d(${panX.toFixed(1)}px, ${panY.toFixed(1)}px, 0)`,
          zIndex: 12,
        }}
      >
        {words.map((w, idx) => {
          const localF = frame - w.startFrame;
          if (localF < -1) {
            return null;
          }

          const isAccent = Boolean(w.accent);
          const isCurrent = idx === activeIdx;
          const isOld = idx < activeIdx - 1;

          const sp = spring({
            frame: Math.max(0, localF),
            fps,
            config: isAccent
              ? { damping: 12, stiffness: 260, mass: 0.55 }
              : { damping: 16, stiffness: 220, mass: 0.6 },
          });

          const baseOpacity = interpolate(localF, [0, 7], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });
          const opacity = isOld && !isAccent ? baseOpacity * 0.58 : baseOpacity;

          const blurPx = interpolate(localF, [0, 10], [isAccent ? 18 : 10, 0], {
            easing: Easing.out(Easing.quad),
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });

          const scale = isAccent
            ? interpolate(sp, [0, 1], [1.34, isCurrent ? 1.05 : 1.0])
            : interpolate(sp, [0, 1], [0.85, isCurrent ? 1.03 : 1.0]);

          // Diagonal staircase with intentional editorial stagger (never overlaps edges)
          const t = count === 1 ? 0.5 : idx / (count - 1);
          const topPct = 24 + t * 44; // 24% -> 68%
          const zigzagX = idx % 2 === 0 ? 22 + t * 22 : 44 + t * 18; // staggered editorial cascade
          const tiltDeg = isAccent ? -1.8 : idx % 2 === 0 ? -1.4 : 1.4;
          const hasDigits = /[0-9₹%]/.test(w.text);
          const wordSize = isAccent ? Math.round(fontSize * 1.62) : Math.round(fontSize * 0.96);

          return (
            <div
              key={`${idx}-${w.text}`}
              style={{
                position: 'absolute',
                top: `${topPct.toFixed(1)}%`,
                left: `${zigzagX.toFixed(1)}%`,
                transform: `translate(-40%, -50%) rotate(${tiltDeg}deg) scale(${scale.toFixed(4)})`,
                paddingTop: 22,
                paddingBottom: 22,
                paddingLeft: 14,
                paddingRight: 14,
                opacity,
                filter: blurPx > 0.15 ? `blur(${blurPx.toFixed(2)}px)` : undefined,
                fontFamily: isAccent
                  ? hasDigits
                    ? FONTS.displayKinetic
                    : FONTS.displaySerif
                  : FONTS.bodyMarathi,
                fontWeight: isAccent ? (hasDigits ? 900 : 700) : 600,
                fontSize: wordSize,
                lineHeight: 1.5,
                color: isAccent ? (w.accentColor ?? '#0D3494') : '#1A1C20',
                whiteSpace: 'nowrap',
                textShadow: isAccent ? '0 8px 24px rgba(0,0,0,0.12)' : 'none',
                willChange: 'transform, opacity, filter',
              }}
            >
              {w.text}
            </div>
          );
        })}

        {subLabel ? (
          <div
            style={{
              position: 'absolute',
              top: '79%',
              left: '50%',
              transform: 'translateX(-50%)',
              paddingTop: 22,
              paddingBottom: 22,
              paddingLeft: 32,
              paddingRight: 32,
              borderTop: '1.5px solid rgba(26,28,32,0.22)',
              fontFamily: FONTS.displayKinetic,
              fontWeight: 700,
              fontSize: 38,
              lineHeight: 1.48,
              color: '#343840',
              letterSpacing: '0.04em',
              opacity: subOpacity,
              whiteSpace: 'nowrap',
            }}
          >
            {subLabel}
          </div>
        ) : null}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export interface StitchedDarkLine {
  text: string;
  startFrame: number;
  color: string;
  sizePx?: number;
}

/**
 * Reference Video 1 seg_007 dark charcoal stitched dashed-border kinetic card:
 * Grapheme-by-grapheme typewriter slam via Intl.Segmenter + escalating Khand Bold scale
 * + luminous bloom glow + 3D perspective camera settle.
 */
export const StitchedDarkCard: React.FC<{
  lines: StitchedDarkLine[];
  footer?: string;
  footerFrame?: number;
}> = ({ lines, footer, footerFrame = 70 }) => {
  ensureFontsLoaded();
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const cardSpring = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 170, mass: 0.7 },
  });
  const cardScale = interpolate(cardSpring, [0, 1], [0.92, 1.0]);
  const cardRotateZ = interpolate(frame, [0, 140], [-1.6, 0.8], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const cardRotateX = interpolate(cardSpring, [0, 1], [8, 0]);

  return (
    <AbsoluteFill
      style={{
        backgroundColor: '#090A0C',
        justifyContent: 'center',
        alignItems: 'center',
      }}
    >
      <AbsoluteFill
        style={{
          background:
            'radial-gradient(circle at 50% 45%, rgba(255,255,255,0.05) 0%, rgba(9,10,12,0) 62%)',
          pointerEvents: 'none',
        }}
      />

      <div
        style={{
          width: 840,
          minHeight: 1120,
          borderRadius: 92,
          border: '2.5px dashed rgba(244,241,234,0.34)',
          backgroundColor: 'rgba(15,17,21,0.82)',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          paddingLeft: 54,
          paddingRight: 54,
          paddingTop: 64,
          paddingBottom: 64,
          transform: `perspective(1200px) rotateX(${cardRotateX.toFixed(2)}deg) rotateZ(${cardRotateZ.toFixed(2)}deg) scale(${cardScale.toFixed(4)})`,
          boxShadow: '0 32px 96px rgba(0,0,0,0.72)',
          zIndex: 14,
        }}
      >
        {lines.map((line, idx) => {
          const localF = frame - line.startFrame;
          if (localF < -1) {
            return null;
          }
          const graphemes = splitMarathiAksharas(line.text);
          const revealFrames = Math.max(10, Math.min(22, graphemes.length * 2));
          const shownCount = Math.min(
            graphemes.length,
            Math.max(1, Math.floor(interpolate(localF, [0, revealFrames], [1, graphemes.length + 0.99], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            })))
          );
          const revealedText = graphemes.slice(0, shownCount).join('');

          const sp = spring({
            frame: Math.max(0, localF),
            fps,
            config: { damping: 12, stiffness: 260, mass: 0.55 },
          });
          const scale = interpolate(sp, [0, 1], [1.24, 1.0]);
          const blurPx = interpolate(localF, [0, 8], [10, 0], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });

          // Escalating poster scale hierarchy (Reference Video 1 seg_007)
          const escalatedSize =
            line.sizePx ?? (idx === 0 ? 64 : idx === 1 ? 86 : 108);

          return (
            <div
              key={idx}
              style={{
                fontFamily: FONTS.displayKinetic,
                fontWeight: 900,
                fontSize: escalatedSize,
                lineHeight: 1.46,
                paddingTop: 22,
                paddingBottom: 22,
                marginTop: idx > 0 ? -24 : 0,
                color: line.color,
                textAlign: 'center',
                transform: `scale(${scale.toFixed(4)})`,
                filter: blurPx > 0.15 ? `blur(${blurPx.toFixed(2)}px)` : undefined,
                textShadow: `0 0 32px ${line.color}66, 0 8px 30px rgba(0,0,0,0.75)`,
                willChange: 'transform, filter',
              }}
            >
              {revealedText}
            </div>
          );
        })}

        {footer ? (
          <div
            style={{
              marginTop: 28,
              paddingTop: 22,
              paddingBottom: 22,
              fontFamily: FONTS.displaySerif,
              fontWeight: 600,
              fontSize: 38,
              lineHeight: 1.48,
              color: 'rgba(244,241,234,0.76)',
              textAlign: 'center',
              opacity: interpolate(frame, [footerFrame, footerFrame + 14], [0, 1], {
                extrapolateLeft: 'clamp',
                extrapolateRight: 'clamp',
              }),
            }}
          >
            {footer}
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};

/**
 * Reference Video 1 seg_006 translucent colored paper highlighter strip sliding smoothly across top band.
 */
export const HighlighterRibbon: React.FC<{
  text: string;
  colorRgba: string;
  topPx?: number;
}> = ({ text, colorRgba, topPx = 220 }) => {
  ensureFontsLoaded();
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const ribbonIn = spring({
    frame,
    fps,
    config: { damping: 16, stiffness: 190, mass: 0.7 },
  });
  const translateX = interpolate(frame, [0, 220], [160, -160], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const scaleX = interpolate(ribbonIn, [0, 1], [0.2, 1]);

  return (
    <div
      style={{
        position: 'absolute',
        top: topPx,
        left: -60,
        right: -60,
        backgroundColor: colorRgba,
        paddingTop: 22,
        paddingBottom: 22,
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        transform: `rotate(-1.5deg) scaleX(${scaleX.toFixed(4)})`,
        transformOrigin: '0% 50%',
        boxShadow: '0 10px 28px rgba(0,0,0,0.32)',
        zIndex: 22,
        pointerEvents: 'none',
      }}
    >
      <div
        style={{
          fontFamily: FONTS.displayKinetic,
          fontWeight: 800,
          fontSize: 44,
          lineHeight: 1.45,
          color: '#FAF8F4',
          letterSpacing: '0.04em',
          whiteSpace: 'nowrap',
          transform: `translate3d(${translateX.toFixed(1)}px, 0, 0)`,
        }}
      >
        {text}
      </div>
    </div>
  );
};

/**
 * Kinetic Editorial Hero Numeral Slam:
 * Expressive Khand Bold condensed display numerals with spring slam, directional motion-blur snap,
 * and an animated editorial accent hairline sweeping underneath.
 */
export const EditorialHeroNumber: React.FC<{
  value: string;
  label?: string;
  startFrame: number;
  topPercent?: number;
  leftPercent?: number;
  color: string;
  labelColor?: string;
  fontSize?: number;
  darkShadow?: boolean;
}> = ({
  value,
  label,
  startFrame,
  topPercent = 18,
  leftPercent = 50,
  color,
  labelColor = '#4D525B',
  fontSize = 96,
  darkShadow = false,
}) => {
  ensureFontsLoaded();
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const localF = frame - startFrame;
  if (localF < -1) {
    return null;
  }

  const sp = spring({
    frame: Math.max(0, localF),
    fps,
    config: { damping: 12, stiffness: 260, mass: 0.58 },
  });
  const opacity = interpolate(localF, [0, 6], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const scale = interpolate(sp, [0, 1], [1.36, 1.0]);
  const dy = interpolate(sp, [0, 1], [28, 0]);
  const blurPx = interpolate(localF, [0, 10], [16, 0], {
    easing: Easing.out(Easing.quad),
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const ruleProgress = interpolate(localF, [6, 22], [0, 1], {
    easing: Easing.out(Easing.cubic),
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        top: `${topPercent}%`,
        left: `${leftPercent}%`,
        transform: `translate(-50%, 0) translate3d(0, ${dy.toFixed(1)}px, 0) scale(${scale.toFixed(4)})`,
        opacity,
        filter: blurPx > 0.15 ? `blur(${blurPx.toFixed(2)}px)` : undefined,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        paddingTop: 22,
        paddingBottom: 22,
        zIndex: 25,
        pointerEvents: 'none',
      }}
    >
      {label ? (
        <div
          style={{
            fontFamily: FONTS.bodyMarathi,
            fontWeight: 800,
            fontSize: 32,
            lineHeight: 1.46,
            color: labelColor,
            letterSpacing: '0.03em',
            textShadow: darkShadow ? '0 2px 14px rgba(0,0,0,0.82)' : 'none',
            marginBottom: -8,
            whiteSpace: 'nowrap',
          }}
        >
          {label}
        </div>
      ) : null}
      <div
        style={{
          fontFamily: FONTS.displayKinetic,
          fontWeight: 900,
          fontSize: Math.round(fontSize * 1.16),
          lineHeight: 1.45,
          color,
          fontVariantNumeric: 'tabular-nums',
          letterSpacing: '-0.01em',
          textShadow: darkShadow
            ? `0 0 28px ${color}66, 0 8px 32px rgba(0,0,0,0.90)`
            : '0 6px 20px rgba(0,0,0,0.12)',
          whiteSpace: 'nowrap',
        }}
      >
        {value}
      </div>
      <div
        style={{
          width: `${Math.round(ruleProgress * 100)}%`,
          maxWidth: 260,
          height: 4,
          borderRadius: 2,
          marginTop: -12,
          backgroundColor: color,
          opacity: 0.72,
        }}
      />
    </div>
  );
};

/**
 * Clearly visible circular RIGHT INVESTMENT brand corner mark (124x124px, opacity 0.94).
 */
export const RestrainedCornerBug: React.FC<{ fadeInFrames?: number }> = ({
  fadeInFrames = 0,
}) => {
  const frame = useCurrentFrame();
  const opacity =
    fadeInFrames > 0
      ? interpolate(frame, [0, fadeInFrames], [0, 0.94], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        })
      : 0.94;

  return (
    <Img
      src={staticFile('assets/images/right_investment_logo.png')}
      style={{
        position: 'absolute',
        top: 56,
        right: 44,
        width: 124,
        height: 124,
        opacity,
        filter: 'drop-shadow(0 8px 20px rgba(0,0,0,0.45))',
        zIndex: 40,
        pointerEvents: 'none',
      }}
    />
  );
};

/**
 * Reference Video 2 bed-scene homage: crisp cash-slip badge above the pillow
 * slammed by a clean pure-vector red prohibition stamp.
 */
export const BedProhibitionBadge: React.FC<{
  stampFrame: number;
  label: string;
}> = ({ stampFrame, label }) => {
  ensureFontsLoaded();
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const cardIn = spring({
    frame,
    fps,
    config: { damping: 16, stiffness: 180 },
  });
  const stampLocal = frame - stampFrame;
  const stampSp = spring({
    frame: Math.max(0, stampLocal),
    fps,
    config: { damping: 11, stiffness: 280, mass: 0.5 },
  });
  const stampScale = interpolate(stampSp, [0, 1], [2.1, 1.0]);
  const stampOpacity = interpolate(stampLocal, [0, 4], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        top: 176,
        left: '50%',
        transform: `translateX(-50%) scale(${interpolate(cardIn, [0, 1], [0.85, 1]).toFixed(4)})`,
        backgroundColor: '#E8E4D8',
        border: '3px solid #2A2C2E',
        borderRadius: 18,
        paddingTop: 22,
        paddingBottom: 22,
        paddingLeft: 42,
        paddingRight: 42,
        boxShadow: '0 14px 36px rgba(0,0,0,0.55)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 18,
        zIndex: 26,
      }}
    >
      <span
        style={{
          fontFamily: FONTS.displayKinetic,
          fontWeight: 800,
          fontSize: 44,
          lineHeight: 1.45,
          color: '#1C1E22',
          whiteSpace: 'nowrap',
        }}
      >
        {label}
      </span>

      <div
        style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          opacity: stampOpacity,
          transform: `scale(${stampScale.toFixed(4)}) rotate(-8deg)`,
          pointerEvents: 'none',
        }}
      >
        <svg width={108} height={108} viewBox="0 0 100 100">
          <circle
            cx="50"
            cy="50"
            r="41"
            fill="none"
            stroke="#C91D1D"
            strokeWidth="11"
          />
          <line
            x1="21"
            y1="21"
            x2="79"
            y2="79"
            stroke="#C91D1D"
            strokeWidth="11"
            strokeLinecap="round"
          />
        </svg>
      </div>
    </div>
  );
};
