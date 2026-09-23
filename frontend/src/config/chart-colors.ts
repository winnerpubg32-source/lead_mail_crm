/**
 * Chart palette.
 *
 * Hand-picked hex values that stay legible on both the light and the dark
 * surface. Kept in one module so charts, badges and legends stay in sync when
 * the brand evolves.
 */
export const chartPalette = {
  brand: '#6366f1',
  brandSoft: '#a5b4fc',
  sky: '#0ea5e9',
  emerald: '#10b981',
  amber: '#f59e0b',
  rose: '#f43f5e',
  violet: '#8b5cf6',
  slate: '#94a3b8',
  cyan: '#06b6d4',
  teal: '#14b8a6',
} as const;

export type ChartColor = (typeof chartPalette)[keyof typeof chartPalette];

/** Ordered series used by the lead-source donut and its legend. */
export const sourceSeriesColors: string[] = [
  chartPalette.brand,
  chartPalette.sky,
  chartPalette.emerald,
  chartPalette.violet,
  chartPalette.amber,
  chartPalette.teal,
];

/** Funnel/pipeline stage colour ramp (brand tints from dark to light). */
export const pipelineRamp: string[] = [
  chartPalette.brand,
  '#818cf8',
  chartPalette.sky,
  chartPalette.emerald,
  chartPalette.amber,
];
