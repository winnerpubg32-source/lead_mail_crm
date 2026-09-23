import { useEffect } from 'react';

import { env } from '@/lib/env';

/** Keep the browser tab title in sync with the active page. */
export function useDocumentTitle(title?: string): void {
  useEffect(() => {
    document.title = title ? `${title} · ${env.appName}` : env.appName;
  }, [title]);
}
