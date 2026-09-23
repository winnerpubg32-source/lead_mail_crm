/**
 * Theme store.
 *
 * Implemented as a tiny external store (not React state) for two reasons:
 *  - every component that calls `useTheme()` shares the same preference, so the
 *    topbar toggle and the settings page never disagree;
 *  - the OS preference is an external source of truth, which is exactly what
 *    `useSyncExternalStore` is designed for.
 */

export type Theme = 'light' | 'dark';
export type ThemePreference = Theme | 'system';

export const THEME_STORAGE_KEY = 'outreachos.theme';

function readStoredPreference(): ThemePreference {
  if (typeof localStorage === 'undefined') return 'system';
  try {
    const stored = localStorage.getItem(THEME_STORAGE_KEY);
    return stored === 'light' || stored === 'dark' ? stored : 'system';
  } catch {
    return 'system';
  }
}

let preference: ThemePreference = readStoredPreference();
const listeners = new Set<() => void>();

export const themeStore = {
  subscribe(listener: () => void): () => void {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },

  getPreference(): ThemePreference {
    return preference;
  },

  setPreference(next: ThemePreference): void {
    preference = next;
    try {
      if (next === 'system') {
        localStorage.removeItem(THEME_STORAGE_KEY);
      } else {
        localStorage.setItem(THEME_STORAGE_KEY, next);
      }
    } catch {
      /* storage unavailable — the session keeps the in-memory value */
    }
    listeners.forEach((listener) => listener());
  },
};

/** Applies the resolved theme to the document (class + color-scheme). */
export function applyThemeToDocument(theme: Theme): void {
  const root = document.documentElement;
  root.classList.toggle('dark', theme === 'dark');
  root.style.colorScheme = theme;
}
