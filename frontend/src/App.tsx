import { QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';

import { ErrorBoundary } from '@/components/feedback/ErrorBoundary';
import { queryClient } from '@/lib/query-client';
import { AppRoutes } from '@/routes/AppRoutes';

/**
 * Application root: query provider (server state) + router (navigation).
 * UI state such as the theme lives in hooks and does not need a provider.
 */
export function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;
