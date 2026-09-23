import { useEffect, useState } from 'react';

/**
 * Debounce a rapidly changing value (search boxes).
 *
 * Keeps a keystroke from firing a request per character while still updating
 * the input immediately.
 */
export function useDebouncedValue<T>(value: T, delayMs = 350): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(value), delayMs);
    return () => window.clearTimeout(timer);
  }, [value, delayMs]);

  return debounced;
}
