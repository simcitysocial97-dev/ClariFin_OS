/**
 * Recharts - Shared dynamic imports for Recharts components
 *
 * All charts should import from this module to ensure:
 * - Consistent SSR handling
 * - Type safety
 * - Single source of truth for component imports
 */

import dynamic from 'next/dynamic';

// Type-safe dynamic imports for recharts components
// All components use ssr: false to prevent SSR issues
// loading: () => null to prevent flash of empty content

export const ComposedChart = dynamic(
  () => import('recharts').then((mod) => mod.ComposedChart),
  { ssr: false, loading: () => null }
) as typeof import('recharts').ComposedChart;

export const BarChart = dynamic(
  () => import('recharts').then((mod) => mod.BarChart),
  { ssr: false, loading: () => null }
) as typeof import('recharts').BarChart;

export const LineChart = dynamic(
  () => import('recharts').then((mod) => mod.LineChart),
  { ssr: false, loading: () => null }
) as typeof import('recharts').LineChart;

export const Bar = dynamic(
  () => import('recharts').then((mod) => mod.Bar),
  { ssr: false, loading: () => null }
) as typeof import('recharts').Bar;

export const Line = dynamic(
  () => import('recharts').then((mod) => mod.Line),
  { ssr: false, loading: () => null }
) as typeof import('recharts').Line;

export const XAxis = dynamic(
  () => import('recharts').then((mod) => mod.XAxis),
  { ssr: false, loading: () => null }
) as typeof import('recharts').XAxis;

export const YAxis = dynamic(
  () => import('recharts').then((mod) => mod.YAxis),
  { ssr: false, loading: () => null }
) as typeof import('recharts').YAxis;

export const CartesianGrid = dynamic(
  () => import('recharts').then((mod) => mod.CartesianGrid),
  { ssr: false, loading: () => null }
) as typeof import('recharts').CartesianGrid;

export const Tooltip = dynamic(
  () => import('recharts').then((mod) => mod.Tooltip),
  { ssr: false, loading: () => null }
) as typeof import('recharts').Tooltip;

export const ResponsiveContainer = dynamic(
  () => import('recharts').then((mod) => mod.ResponsiveContainer),
  { ssr: false, loading: () => null }
) as typeof import('recharts').ResponsiveContainer;

export const Legend = dynamic(
  () => import('recharts').then((mod) => mod.Legend),
  { ssr: false, loading: () => null }
) as typeof import('recharts').Legend;