import { fileURLToPath, URL } from 'node:url';

import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import { defineConfig, loadEnv } from 'vite';

/**
 * Vite configuration for OutreachOS.
 *
 * The dev server binds to 0.0.0.0 and proxies `/api` to Django so the browser
 * only ever talks to a single origin (required for preview environments and for
 * avoiding CORS in local development).
 */
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const apiTarget = env.VITE_PROXY_TARGET ?? env.DJANGO_PROXY_TARGET ?? 'http://127.0.0.1:8000';
  const port = Number(env.VITE_PORT ?? 5173);

  return {
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    server: {
      host: '0.0.0.0',
      port,
      strictPort: false,
      // Preview hosts are proxied through https://<port>-<sandbox>.e2b.app
      allowedHosts: true,
      hmr: { clientPort: Number(env.VITE_HMR_CLIENT_PORT ?? port) },
      proxy: {
        '/api': { target: apiTarget, changeOrigin: true },
        '/admin': { target: apiTarget, changeOrigin: true },
        '/static': { target: apiTarget, changeOrigin: true },
      },
    },
    preview: {
      host: '0.0.0.0',
      port,
      allowedHosts: true,
    },
    build: {
      outDir: 'dist',
      sourcemap: mode !== 'production',
    },
  };
});
