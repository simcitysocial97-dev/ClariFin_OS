'use client';

/**
 * Recharts Components - Dynamic Imports
 * =====================================
 *
 * Wrapper module for Recharts dynamic imports.
 * The 'as unknown as' casting works around next/dynamic + recharts type issues.
 */

import dynamic from 'next/dynamic';

// We use 'as unknown as React.FC' to bypass complex recharts type incompatibilities
// This is a pragmatic solution for third-party library integration
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const dyn = (loader: () => Promise<any>) => dynamic(loader, { ssr: false }) as unknown as React.FC<any>;

export const BarChart = dyn(() => import('recharts').then((mod) => mod.BarChart));
export const AreaChart = dyn(() => import('recharts').then((mod) => mod.AreaChart));
export const LineChart = dyn(() => import('recharts').then((mod) => mod.LineChart));
export const ComposedChart = dyn(() => import('recharts').then((mod) => mod.ComposedChart));
export const PieChart = dyn(() => import('recharts').then((mod) => mod.PieChart));
export const Bar = dyn(() => import('recharts').then((mod) => mod.Bar));
export const Area = dyn(() => import('recharts').then((mod) => mod.Area));
export const Line = dyn(() => import('recharts').then((mod) => mod.Line));
export const Pie = dyn(() => import('recharts').then((mod) => mod.Pie));
export const XAxis = dyn(() => import('recharts').then((mod) => mod.XAxis));
export const YAxis = dyn(() => import('recharts').then((mod) => mod.YAxis));
export const CartesianGrid = dyn(() => import('recharts').then((mod) => mod.CartesianGrid));
export const Tooltip = dyn(() => import('recharts').then((mod) => mod.Tooltip));
export const Legend = dyn(() => import('recharts').then((mod) => mod.Legend));
export const ResponsiveContainer = dyn(() => import('recharts').then((mod) => mod.ResponsiveContainer));
export const Cell = dyn(() => import('recharts').then((mod) => mod.Cell));
