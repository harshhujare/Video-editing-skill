import React from 'react';
import { Easing, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import { FONTS, SWISS_PALETTE, ensureFontsLoaded, splitMarathiAksharas } from '../styles/fonts';

export interface CaptionToken {
  text: string;
  bold?: boolean;
  accentColor?: string;
}

export interface CaptionCardSpec {
  /** Local start frame inside the scene (>= 0) */
  startFrame: number;
  /** Local end frame inside the scene (duration >= 24) */
  endFrame: number;
  tokens: CaptionToken[];
}

export const SWISS_EASE = Easing.bezier(0.7, 0, 0.2, 1);

const renderTokenText = (
  token: CaptionToken,
  key: number,
  baseFontSize: number,
  baseColor: string,
  boldColor: string
) => {
  const aksharas = splitMarathiAksharas(token.text);
  const safeText = aksharas.join('');
  return (
    <span
      key={key}
      style={{
        fontFamily: FONTS.bodyMarathi,
        fontWeight: token.bold ? 800 : 600,
        fontSize: token.bold ? baseFontSize + 4 : baseFontSize,
        color: token.bold ? token.accentColor ?? boldColor : baseColor,
        letterSpacing: token.bold ? '0.01em' : '0em',
        marginRight: 11,
        display: 'inline-block',
      }}
    >
      {safeText}
    </span>
  );
};

export interface ArollCaptionBarProps {
  cards: CaptionCardSpec[];
  top?: number;
  maxWidth?: number;
}

/**
 * Sleek dark-frosted editorial caption pill for talking-head A-roll scenes.
 * Strictly uses Mukta SemiBold (600) + Mukta ExtraBold (800) — zero hard wireframe borders.
 */
export const ArollCaptionBar: React.FC<ArollCaptionBarProps> = ({
  cards,
  top = 1215,
  maxWidth = 820,
}) => {
  ensureFontsLoaded();
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const active =
    cards.find((c) => frame >= c.startFrame && frame < c.endFrame) ??
    cards[cards.length - 1];
  if (!active) return null;

  const localF = Math.max(0, frame - active.startFrame);
  const pop = spring({
    frame: localF,
    fps,
    config: { damping: 16, stiffness: 280, mass: 0.55 },
  });
  const translateY = interpolate(pop, [0, 1], [8, 0]);
  const scale = interpolate(pop, [0, 1], [0.97, 1]);

  return (
    <div
      style={{
        position: 'absolute',
        top,
        left: '50%',
        width: maxWidth,
        transform: `translate3d(-50%, ${translateY.toFixed(2)}px, 0) scale(${scale.toFixed(4)})`,
        display: 'flex',
        justifyContent: 'center',
        zIndex: 40,
        pointerEvents: 'none',
      }}
    >
      <div
        style={{
          backgroundColor: 'rgba(13, 15, 18, 0.78)',
          backdropFilter: 'blur(14px)',
          border: '1px solid rgba(255, 255, 255, 0.14)',
          borderRadius: 16,
          paddingTop: 20,
          paddingBottom: 20,
          paddingLeft: 30,
          paddingRight: 30,
          boxShadow: '0 20px 50px rgba(13, 15, 18, 0.30)',
          textAlign: 'center',
          lineHeight: 1.48,
          maxWidth,
        }}
      >
        {active.tokens.map((tok, i) =>
          renderTokenText(tok, i, 38, '#F5F3EE', '#FFFFFF')
        )}
      </div>
    </div>
  );
};

export interface EditorialCaptionFooterProps {
  cards: CaptionCardSpec[];
  dark?: boolean;
  top?: number;
  left?: number;
  width?: number;
}

/**
 * Sleek dark-frosted editorial caption pill for illustrated / dataviz scenes.
 * Zero hard black borders or offset neo-brutalist shadows.
 */
export const EditorialCaptionFooter: React.FC<EditorialCaptionFooterProps> = ({
  cards,
  dark = false,
  top = 1140,
  left = 100,
  width = 860,
}) => {
  ensureFontsLoaded();
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const active =
    cards.find((c) => frame >= c.startFrame && frame < c.endFrame) ??
    cards[cards.length - 1];
  if (!active) return null;

  const localF = Math.max(0, frame - active.startFrame);
  const pop = spring({
    frame: localF,
    fps,
    config: { damping: 18, stiffness: 260, mass: 0.6 },
  });
  const translateY = interpolate(pop, [0, 1], [8, 0]);

  return (
    <div
      style={{
        position: 'absolute',
        top,
        left,
        width,
        transform: `translate3d(0, ${translateY.toFixed(2)}px, 0)`,
        display: 'flex',
        justifyContent: 'center',
        zIndex: 40,
      }}
    >
      <div
        style={{
          backgroundColor: dark ? 'rgba(20, 24, 32, 0.86)' : 'rgba(13, 15, 18, 0.82)',
          backdropFilter: 'blur(12px)',
          border: '1px solid rgba(255, 255, 255, 0.14)',
          boxShadow: '0 20px 48px rgba(13, 15, 18, 0.18)',
          borderRadius: 16,
          paddingTop: 20,
          paddingBottom: 20,
          paddingLeft: 28,
          paddingRight: 28,
          textAlign: 'center',
          lineHeight: 1.48,
          width: '100%',
        }}
      >
        {active.tokens.map((tok, i) =>
          renderTokenText(tok, i, 37, '#F5F3EE', '#93C5FD')
        )}
      </div>
    </div>
  );
};

export const AmfiDisclaimer: React.FC<{ dark?: boolean; top?: number; left?: number; width?: number }> = ({
  dark = false,
  top = 1345,
  left = 90,
  width = 860,
}) => {
  ensureFontsLoaded();
  return (
    <div
      style={{
        position: 'absolute',
        top,
        left,
        width,
        textAlign: 'center',
        fontFamily: FONTS.tabular,
        fontWeight: 400,
        fontSize: 18,
        lineHeight: 1.42,
        color: dark ? 'rgba(245, 243, 238, 0.68)' : 'rgba(20, 22, 25, 0.68)',
        zIndex: 40,
      }}
    >
      Mutual Fund investments are subject to market risks. Past performance (2022–26 illustration) is not guaranteed.
    </div>
  );
};

export interface SwissHeaderStripProps {
  kicker: string;
  title: string;
  dark?: boolean;
  accentColor?: string;
  top?: number;
  left?: number;
  width?: number;
}

/**
 * Sleek translucent editorial masthead pill inside Reels safe zone (y >= 220, x: 90..950).
 */
export const SwissHeaderStrip: React.FC<SwissHeaderStripProps> = ({
  kicker,
  title,
  dark = false,
  accentColor = SWISS_PALETTE.cobalt,
  top = 225,
  left = 90,
  width = 860,
}) => {
  ensureFontsLoaded();
  return (
    <div
      style={{
        position: 'absolute',
        top,
        left,
        width,
        backgroundColor: dark ? 'rgba(20, 24, 32, 0.82)' : 'rgba(245, 243, 238, 0.92)',
        backdropFilter: 'blur(12px)',
        border: dark ? '1px solid rgba(255, 255, 255, 0.12)' : '1px solid rgba(20, 22, 25, 0.08)',
        boxShadow: '0 14px 36px rgba(13, 15, 18, 0.10)',
        borderRadius: 16,
        paddingTop: 14,
        paddingBottom: 14,
        paddingLeft: 20,
        paddingRight: 20,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 14,
        zIndex: 35,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
        <div
          style={{
            backgroundColor: accentColor,
            color: '#FFFFFF',
            fontFamily: FONTS.tabular,
            fontWeight: 700,
            fontSize: 17,
            letterSpacing: '0.07em',
            padding: '6px 14px',
            borderRadius: 10,
            whiteSpace: 'nowrap',
          }}
        >
          {kicker}
        </div>
        <div
          style={{
            fontFamily: FONTS.bodyMarathi,
            fontWeight: 800,
            fontSize: 27,
            lineHeight: 1.44,
            color: dark ? '#F5F3EE' : SWISS_PALETTE.ink,
          }}
        >
          {title}
        </div>
      </div>
    </div>
  );
};

export interface SharedDarkDatavizGridProps {
  mfProgress: number;
  mfOpacity?: number;
  poProgress?: number;
  showMfPeakCallout?: boolean;
  showPoLabel?: boolean;
  frozenPassbookOpacity?: number;
}

const MF_POINTS: [number, number][] = [
  [130, 615], // 2022: ₹15.0L
  [295, 504], // 2023: ₹16.1L
  [460, 376], // 2024: ₹17.4L
  [625, 238], // 2025: ₹18.8L
  [790, 95],  // 2026: ₹20.0L
];

const PO_POINTS: [number, number][] = [
  [130, 615],
  [790, 615],
];

function polylinePath(points: [number, number][]): string {
  return points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p[0]} ${p[1]}`).join(' ');
}

/**
 * Taller 760px shared #0D0F12 coordinate grid used by both Scene08 (₹20L growth)
 * and Scene09 (₹0 flatline + frozen passbook badge) to fill vertical frame cleanly.
 */
export const SharedDarkDatavizGrid: React.FC<SharedDarkDatavizGridProps> = ({
  mfProgress,
  mfOpacity = 1,
  poProgress = 0,
  showMfPeakCallout = false,
  showPoLabel = false,
  frozenPassbookOpacity = 0,
}) => {
  ensureFontsLoaded();

  const mfTotalLen = 890;
  const mfDashOffset = mfTotalLen * (1 - Math.max(0, Math.min(1, mfProgress)));
  const poTotalLen = 660;
  const poDashOffset = poTotalLen * (1 - Math.max(0, Math.min(1, poProgress)));

  const yLevels = [
    { val: '₹20L', y: 95 },
    { val: '₹19L', y: 199 },
    { val: '₹18L', y: 303 },
    { val: '₹17L', y: 407 },
    { val: '₹16L', y: 511 },
    { val: '₹15L', y: 615 },
  ];
  const xYears = [
    { yr: '2022', x: 130 },
    { yr: '2023', x: 295 },
    { yr: '2024', x: 460 },
    { yr: '2025', x: 625 },
    { yr: '2026', x: 790 },
  ];

  const clampedMf = Math.max(0, Math.min(1, mfProgress));
  const segFloat = clampedMf * (MF_POINTS.length - 1);
  const segIdx = Math.min(MF_POINTS.length - 2, Math.floor(segFloat));
  const segT = segFloat - segIdx;
  const tipX = MF_POINTS[segIdx][0] + (MF_POINTS[segIdx + 1][0] - MF_POINTS[segIdx][0]) * segT;
  const tipY = MF_POINTS[segIdx][1] + (MF_POINTS[segIdx + 1][1] - MF_POINTS[segIdx][1]) * segT;
  const poTipX = 130 + (790 - 130) * Math.max(0, Math.min(1, poProgress));

  return (
    <div
      style={{
        position: 'absolute',
        top: 315,
        left: 90,
        width: 880,
        height: 760,
        backgroundColor: 'rgba(20, 24, 32, 0.78)',
        border: '1px solid rgba(245, 243, 238, 0.12)',
        borderRadius: 24,
        boxShadow: '0 24px 60px rgba(0, 0, 0, 0.45)',
        zIndex: 25,
        overflow: 'hidden',
      }}
    >
      <svg width={880} height={760} viewBox="0 0 880 760" style={{ overflow: 'visible' }}>
        <defs>
          <pattern id="halftonePeak" width="10" height="10" patternUnits="userSpaceOnUse">
            <circle cx="5" cy="5" r="2.2" fill="#16A34A" opacity="0.35" />
          </pattern>
        </defs>

        {yLevels.map((lvl) => (
          <g key={lvl.val}>
            <line
              x1={110}
              y1={lvl.y}
              x2={820}
              y2={lvl.y}
              stroke={lvl.val === '₹15L' ? 'rgba(245,243,238,0.34)' : 'rgba(245,243,238,0.11)'}
              strokeWidth={lvl.val === '₹15L' ? 1.6 : 1}
              strokeDasharray={lvl.val === '₹15L' ? undefined : '4 6'}
            />
            <text
              x={96}
              y={lvl.y + 7}
              textAnchor="end"
              fill={
                lvl.val === '₹20L'
                  ? '#4ADE80'
                  : lvl.val === '₹15L'
                    ? '#F5F3EE'
                    : 'rgba(245,243,238,0.56)'
              }
              fontFamily={FONTS.tabular}
              fontWeight={700}
              fontSize={22}
            >
              {lvl.val}
            </text>
          </g>
        ))}

        {xYears.map((item) => (
          <g key={item.yr}>
            <line
              x1={item.x}
              y1={64}
              x2={item.x}
              y2={640}
              stroke="rgba(245,243,238,0.09)"
              strokeWidth={1}
            />
            <text
              x={item.x}
              y={692}
              textAnchor="middle"
              fill="rgba(245,243,238,0.78)"
              fontFamily={FONTS.tabular}
              fontWeight={700}
              fontSize={22}
            >
              {item.yr}
            </text>
          </g>
        ))}

        {showMfPeakCallout && mfOpacity > 0.5 && (
          <circle cx={790} cy={95} r={62} fill="url(#halftonePeak)" />
        )}

        {mfProgress > 0 && (
          <g opacity={mfOpacity}>
            <path
              d={polylinePath(MF_POINTS)}
              fill="none"
              stroke={SWISS_PALETTE.emerald}
              strokeWidth={7}
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeDasharray={mfTotalLen}
              strokeDashoffset={mfDashOffset}
            />
            {MF_POINTS.map((pt, idx) => {
              const threshold = idx / (MF_POINTS.length - 1);
              if (clampedMf < threshold) return null;
              return (
                <circle
                  key={idx}
                  cx={pt[0]}
                  cy={pt[1]}
                  r={idx === 4 ? 10 : 6.5}
                  fill="#0D0F12"
                  stroke={SWISS_PALETTE.emerald}
                  strokeWidth={3.5}
                />
              );
            })}
            {clampedMf < 0.99 && (
              <circle cx={tipX} cy={tipY} r={9} fill={SWISS_PALETTE.emerald} />
            )}
          </g>
        )}

        {poProgress > 0 && (
          <g>
            <path
              d={polylinePath(PO_POINTS)}
              fill="none"
              stroke={SWISS_PALETTE.crimson}
              strokeWidth={7}
              strokeLinecap="round"
              strokeDasharray={poTotalLen}
              strokeDashoffset={poDashOffset}
            />
            <circle cx={130} cy={615} r={7.5} fill="#0D0F12" stroke={SWISS_PALETTE.crimson} strokeWidth={3.5} />
            <circle cx={poTipX} cy={615} r={9} fill={SWISS_PALETTE.crimson} />
          </g>
        )}

        {showMfPeakCallout && (
          <g transform="translate(560, 26)" opacity={mfOpacity}>
            <rect
              x={0}
              y={0}
              width={245}
              height={76}
              rx={12}
              fill="rgba(20, 24, 32, 0.94)"
              stroke={SWISS_PALETTE.emerald}
              strokeWidth={2}
            />
            <text
              x={18}
              y={33}
              fill="#4ADE80"
              fontFamily={FONTS.tabular}
              fontWeight={700}
              fontSize={22}
            >
              Mutual Fund SWP
            </text>
            <text
              x={18}
              y={62}
              fill="#FFFFFF"
              fontFamily={FONTS.tabular}
              fontWeight={700}
              fontSize={23}
            >
              ₹20 लाख (+₹5L)
            </text>
          </g>
        )}

        {showPoLabel && (
          <g transform="translate(148, 540)">
            <rect
              x={0}
              y={0}
              width={285}
              height={52}
              rx={10}
              fill="rgba(30, 16, 18, 0.94)"
              stroke={SWISS_PALETTE.crimson}
              strokeWidth={1.8}
            />
            <text
              x={16}
              y={33}
              fill="#FCA5A5"
              fontFamily={FONTS.tabular}
              fontWeight={700}
              fontSize={22}
            >
              Post Office · ₹15 लाख (FLAT)
            </text>
          </g>
        )}
      </svg>

      {/* Frozen Passbook Editorial Badge blended cleanly on #0D0F12 beside flatline */}
      {frozenPassbookOpacity > 0.01 && (
        <div
          style={{
            position: 'absolute',
            right: 40,
            bottom: 162,
            width: 210,
            height: 210,
            borderRadius: 28,
            overflow: 'hidden',
            opacity: frozenPassbookOpacity,
            border: '1.5px solid rgba(200, 54, 58, 0.45)',
            boxShadow: '0 18px 45px rgba(0, 0, 0, 0.55)',
            backgroundColor: '#0D0F12',
          }}
        >
          <Img
            src={staticFile('assets/generated/asset_05_frozen_passbook.png')}
            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
          />
        </div>
      )}
    </div>
  );
};

export interface HalftoneStampProps {
  label: string;
  slamFrame: number;
  top?: number;
  left?: number;
}

/**
 * Halftone Dossier crimson rubber stamp slam (2.4x -> 1.0x over 3 frames @ 30fps).
 */
export const HalftoneStamp: React.FC<HalftoneStampProps> = ({
  label,
  slamFrame,
  top = 640,
  left = 440,
}) => {
  ensureFontsLoaded();
  const frame = useCurrentFrame();
  if (frame < slamFrame) return null;

  const localF = frame - slamFrame;
  const slamScale =
    localF <= 3
      ? interpolate(localF, [0, 3], [2.4, 1.0], {
          easing: Easing.in(Easing.cubic),
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        })
      : interpolate(localF, [3, 7], [0.95, 1.0], {
          easing: Easing.out(Easing.cubic),
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        });

  const opacity = interpolate(localF, [0, 2], [0, 0.96], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        top,
        left,
        transform: `translate3d(-50%, -50%, 0) rotate(-7deg) scale(${slamScale.toFixed(3)})`,
        opacity,
        zIndex: 45,
        pointerEvents: 'none',
      }}
    >
      <div
        style={{
          backgroundColor: 'rgba(214, 40, 40, 0.16)',
          border: `5px solid ${SWISS_PALETTE.crimson}`,
          borderRadius: 14,
          padding: '8px',
          boxShadow: '0 20px 44px rgba(0, 0, 0, 0.35)',
        }}
      >
        <div
          style={{
            border: `2.5px dashed ${SWISS_PALETTE.crimson}`,
            borderRadius: 8,
            paddingTop: 20,
            paddingBottom: 20,
            paddingLeft: 34,
            paddingRight: 34,
            backgroundImage:
              'radial-gradient(rgba(214, 40, 40, 0.25) 1.5px, transparent 1.5px)',
            backgroundSize: '8px 8px',
          }}
        >
          <div
            style={{
              fontFamily: FONTS.bodyMarathi,
              fontWeight: 800,
              fontSize: 64,
              lineHeight: 1.44,
              color: '#FF5A5A',
              letterSpacing: '0.02em',
              whiteSpace: 'nowrap',
            }}
          >
            {label}
          </div>
        </div>
      </div>
    </div>
  );
};
