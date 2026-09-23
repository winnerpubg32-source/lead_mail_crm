import { Monitor, Moon, Sun } from 'lucide-react';

import { useTheme, type ThemePreference } from '@/hooks/useTheme';
import { cn } from '@/lib/utils/cn';

const options: Array<{ value: ThemePreference; label: string; icon: typeof Sun }> = [
  { value: 'light', label: 'Light', icon: Sun },
  { value: 'dark', label: 'Dark', icon: Moon },
  { value: 'system', label: 'System', icon: Monitor },
];

/** Three-state theme switcher (light / dark / follow system). */
export function ThemeToggle({ compact = false }: { compact?: boolean }) {
  const { preference, setPreference } = useTheme();

  if (compact) {
    return (
      <div className="inline-flex items-center gap-0.5 rounded-lg border border-border-subtle bg-surface-2 p-0.5">
        {options.map(({ value, label, icon: Icon }) => (
          <button
            key={value}
            type="button"
            aria-label={`${label} theme`}
            aria-pressed={preference === value}
            onClick={() => setPreference(value)}
            className={cn(
              'grid size-7 place-items-center rounded-md transition-colors',
              preference === value
                ? 'bg-surface text-fg shadow-[var(--shadow-card)]'
                : 'text-subtle hover:text-fg',
            )}
          >
            <Icon className="size-3.5" />
          </button>
        ))}
      </div>
    );
  }

  return (
    <div className="flex flex-wrap gap-2">
      {options.map(({ value, label, icon: Icon }) => (
        <button
          key={value}
          type="button"
          onClick={() => setPreference(value)}
          aria-pressed={preference === value}
          className={cn(
            'flex flex-1 items-center gap-2 rounded-lg border px-3 py-2 text-[13px] font-medium transition-colors',
            preference === value
              ? 'border-brand-400 bg-brand-50 text-brand-700 dark:bg-brand-500/10 dark:text-brand-200'
              : 'border-border-subtle text-muted hover:bg-surface-3 hover:text-fg',
          )}
        >
          <Icon className="size-4" />
          {label}
        </button>
      ))}
    </div>
  );
}
