import { useCallback, useSyncExternalStore } from 'react';

/**
 * Subscribe to a CSS media query.
 *
 * `useSyncExternalStore` keeps the value in sync with the browser without
 * setState-in-effect cascades, and returns the server snapshot for SSR safety.
 */
export function useMediaQuery(query: string): boolean {
  const subscribe = useCallback(
    (onStoreChange: () => void) => {
      const media = window.matchMedia(query);
      media.addEventListener('change', onStoreChange);
      return () => media.removeEventListener('change', onStoreChange);
    },
    [query],
  );

  const getSnapshot = useCallback(() => window.matchMedia(query).matches, [query]);

  return useSyncExternalStore(subscribe, getSnapshot, () => false);
}

/** Convenience wrappers matching the Tailwind breakpoints used in the app. */
export const useIsMobile = () => useMediaQuery('(max-width: 767px)');
export const useIsTablet = () => useMediaQuery('(max-width: 1023px)');
