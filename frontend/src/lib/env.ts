/**
 * Typed access to the Vite environment.
 *
 * `VITE_USE_MOCK_DATA` is the Phase 1 switch: the dashboard renders realistic
 * placeholder data while the Django endpoints are still being built. Once the
 * API ships, flip it to "false" and the same hooks read from Django.
 */

function readString(key: string, fallback: string): string {
  const value = import.meta.env[key as keyof ImportMetaEnv];
  return typeof value === 'string' && value.length > 0 ? value : fallback;
}

function readBoolean(key: string, fallback: boolean): boolean {
  const value = import.meta.env[key as keyof ImportMetaEnv];
  if (typeof value !== 'string') return fallback;
  return ['1', 'true', 'yes', 'on'].includes(value.toLowerCase());
}

export const env = {
  appName: readString('VITE_APP_NAME', 'OutreachOS'),
  /**
   * Base path every request is resolved against. Defaults to the relative
   * `/api`, which the Vite dev server (and nginx in production) proxies to
   * Django — that keeps the browser on a single origin, so the same build works
   * locally, in Docker and behind any preview/proxy host.
   */
  apiBaseUrl: readString('VITE_API_BASE_URL', '/api'),
  /**
   * Optional absolute API origin for decoupled deployments (e.g. the SPA on a
   * CDN and the API on api.example.com). Leave empty to use the relative path.
   */
  apiUrl: readString('VITE_API_URL', ''),
  useMockData: readBoolean('VITE_USE_MOCK_DATA', true),
  isDevelopment: import.meta.env.DEV,
  isProduction: import.meta.env.PROD,
} as const;

/** Simulated network latency (ms) for the mock data layer so loading states render. */
export const MOCK_LATENCY_MS = 420;
