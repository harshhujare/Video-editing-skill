import React from 'react';
import { COLORS } from '../styles/fonts';

export interface Point2D {
  x: number;
  y: number;
}

export interface TrackedSvgPathProps {
  points: Point2D[];
  progress: number; // 0..1
  strokeColor?: string;
  strokeWidth?: number;
  showNodes?: boolean;
  nodeRadius?: number;
}

export function getPointAlongPolyline(points: Point2D[], progress: number): Point2D {
  if (points.length === 0) return { x: 540, y: 960 };
  if (points.length === 1) return points[0];
  const clamped = Math.max(0, Math.min(1, progress));

  const segLengths: number[] = [];
  let totalLength = 0;
  for (let i = 0; i < points.length - 1; i++) {
    const dx = points[i + 1].x - points[i].x;
    const dy = points[i + 1].y - points[i].y;
    const len = Math.hypot(dx, dy);
    segLengths.push(len);
    totalLength += len;
  }

  if (totalLength === 0) return points[0];
  const targetDist = clamped * totalLength;
  let accum = 0;
  for (let i = 0; i < segLengths.length; i++) {
    const segLen = segLengths[i];
    if (accum + segLen >= targetDist) {
      const localT = segLen > 0 ? (targetDist - accum) / segLen : 0;
      return {
        x: points[i].x + (points[i + 1].x - points[i].x) * localT,
        y: points[i].y + (points[i + 1].y - points[i].y) * localT,
      };
    }
    accum += segLen;
  }
  return points[points.length - 1];
}

export const TrackedSvgPath: React.FC<TrackedSvgPathProps> = ({
  points,
  progress,
  strokeColor = COLORS.accentCobalt,
  strokeWidth = 6,
  showNodes = true,
  nodeRadius = 10,
}) => {
  if (points.length < 2) return null;

  let totalLength = 0;
  for (let i = 0; i < points.length - 1; i++) {
    totalLength += Math.hypot(points[i + 1].x - points[i].x, points[i + 1].y - points[i].y);
  }

  const d = points
    .map((pt, idx) => `${idx === 0 ? 'M' : 'L'} ${pt.x.toFixed(1)} ${pt.y.toFixed(1)}`)
    .join(' ');

  const clamped = Math.max(0, Math.min(1, progress));
  const dashOffset = totalLength * (1 - clamped);
  const tip = getPointAlongPolyline(points, clamped);

  return (
    <svg
      width={1080}
      height={1920}
      viewBox="0 0 1080 1920"
      style={{
        position: 'absolute',
        inset: 0,
        overflow: 'visible',
        pointerEvents: 'none',
      }}
    >
      <path
        d={d}
        fill="none"
        stroke="rgba(18, 19, 22, 0.12)"
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d={d}
        fill="none"
        stroke={strokeColor}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeDasharray={totalLength}
        strokeDashoffset={dashOffset}
      />
      {showNodes &&
        points.map((pt, idx) => {
          const nodeThreshold = idx / Math.max(1, points.length - 1);
          const active = clamped >= nodeThreshold - 0.02;
          return (
            <g key={idx}>
              <circle
                cx={pt.x}
                cy={pt.y}
                r={nodeRadius + 4}
                fill={active ? strokeColor : 'rgba(18, 19, 22, 0.18)'}
              />
              <circle
                cx={pt.x}
                cy={pt.y}
                r={nodeRadius}
                fill={COLORS.paperPure}
                stroke={active ? strokeColor : COLORS.inkMuted}
                strokeWidth={4}
              />
            </g>
          );
        })}
      <circle
        cx={tip.x}
        cy={tip.y}
        r={nodeRadius + 2}
        fill={strokeColor}
      />
    </svg>
  );
};
