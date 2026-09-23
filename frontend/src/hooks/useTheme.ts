import { useCallback, useEffect, useSyncExternalStore } from 'react';

import { useMediaQuery } from '@/hooks/useMediaQuery';
import {
  applyThemeToDocument,
  themeStore,
  type Theme,
  type ThemePreference,
} from '@/lib/theme';

export type { Theme, ThemePreference };

/**
 * Dark/light mode with three states: explicit light, explicit dark, or follow
 * the operating system.
 *
 * The preference lives in a module-level store so every consumer stays in sync;
 * the initial class is applied inline in index.html to avoid a flash.
 */
export function useTheme() {
  const preference = useSyncExternalStore<ThemePreference>(
    themeStore.subscribe,
    themeStore.getPreference,
    () => 'system',
  );
  const systemPrefersDark = useMediaQuery('(prefers-color-scheme: dark)');

  const theme: Theme = preference === 'system' ? (systemPrefersDark ? 'dark' : 'light') : preference;

  // Sync the resolved theme to the document (external system, not React state).
  useEffect(() => {
    applyThemeToDocument(theme);
  }, [theme]);

  const setPreference = useCallback((next: ThemePreference) => themeStore.setPreference(next), []);

  const toggleTheme = useCallback(() => {
    themeStore.setPreference(theme === 'dark' ? 'light' : 'dark');
  }, [theme]);

  return { theme, preference, setPreference, toggleTheme };
}
