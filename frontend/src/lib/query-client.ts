import { QueryClient } from '@tanstack/react-query';

/**
 * Shared React Query client.
 *
 * Server state (Django API) lives here; UI state stays in React context. The
 * defaults below are tuned for a data-dense dashboard: short staleness windows
 * and no refetch storm when switching browser tabs.
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      gcTime: 5 * 60_000,
      retry: 1,
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
    },
    mutations: {
      retry: 0,
    },
  },
});
