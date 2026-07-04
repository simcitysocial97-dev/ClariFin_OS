'use client';

import { useMemo } from 'react';

interface SparklineProps {
  data: number[];
  width?: number;
  height?: number;
  color?: string;
  strokeWidth?: number;
  showArea?: boolean;
}

export function Sparkline({
  data,
  width = 120,
  height = 40,
  color = 'hsl(var(--primary))',
  strokeWidth = 2,
  showArea = true,
}: SparklineProps) {
  const { path, areaPath, min: _min, max: _max } = useMemo(() => {
    if (data.length === 0) return { path: '', areaPath: '', min: 0, max: 0 };

    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1;

    const points = data.map((value, index) => {
      const x = (index / (data.length - 1)) * width;
      const y = height - ((value - min) / range) * height;
      return { x, y };
    });

    const path = points
      .map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`)
      .join(' ');

    const areaPath = `${path} L ${width} ${height} L 0 ${height} Z`;

    return { path, areaPath, min, max };
  }, [data, width, height]);

  if (data.length === 0) return null;

  return (
    <svg width={width} height={height} className="overflow-visible">
      <defs>
        <linearGradient id="sparklineGradient" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.3" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      {showArea && (
        <path
          d={areaPath}
          fill="url(#sparklineGradient)"
          stroke="none"
        />
      )}
      <path
        d={path}
        fill="none"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}