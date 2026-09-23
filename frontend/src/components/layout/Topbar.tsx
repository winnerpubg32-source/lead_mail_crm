import { Bell, Menu, Search } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';

import { ThemeToggle } from '@/components/layout/ThemeToggle';
import { UserMenu } from '@/components/layout/UserMenu';
import { Badge } from '@/components/ui/Badge';
import { findNavItem, navigation } from '@/config/navigation';
import { useHealthStatus } from '@/hooks/useHealthStatus';
import { cn } from '@/lib/utils/cn';

export interface TopbarProps {
  onOpenMobileNav: () => void;
}

/** Backend connectivity pill — reflects `GET /api/health/`. */
function ApiStatusPill() {
  const { isSuccess, isLoading, isError } = useHealthStatus();

  const state = isLoading ? 'checking' : isSuccess ? 'online' : isError ? 'offline' : 'idle';
  const label = state === 'online' ? 'API connected' : state === 'checking' ? 'Checking API' : 'API offline';

  return (
    <span
      title={
        state === 'offline'
          ? 'Django API is not reachable — the dashboard is rendering Phase 1 placeholder data.'
          : label
      }
      className={cn(
        'hidden items-center gap-1.5 rounded-full px-2.5 py-1 text-[11.5px] font-medium ring-1 ring-inset md:inline-flex',
        state === 'online' &&
          'bg-emerald-50 text-emerald-700 ring-emerald-200 dark:bg-emerald-500/10 dark:text-emerald-300 dark:ring-emerald-500/20',
        state === 'offline' &&
          'bg-surface-3 text-muted ring-border-subtle',
        state === 'checking' && 'bg-surface-3 text-muted ring-border-subtle',
      )}
    >
      <span
        aria-hidden="true"
        className={cn(
          'size-1.5 rounded-full',
          state === 'online' ? 'bg-emerald-500' : state === 'checking' ? 'bg-amber-500' : 'bg-slate-400',
        )}
      />
      {label}
    </span>
  );
}

/** Global search is a stub until the lead search endpoints exist. */
function SearchField() {
  const [query, setQuery] = useState('');

  return (
    <div className="relative hidden max-w-md flex-1 items-center md:flex">
      <Search className="pointer-events-none absolute left-3 size-4 text-subtle" />
      <input
        type="search"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="Search leads, companies, contacts…"
        aria-label="Search"
        className="h-9.5 w-full rounded-lg border border-border-subtle bg-surface-2 pl-9 pr-16 text-sm text-fg placeholder:text-subtle focus:border-brand-400 focus:ring-2 focus:ring-brand-500/20 focus:outline-none"
      />
      <kbd className="pointer-events-none absolute right-2.5 rounded border border-border-subtle bg-surface px-1.5 py-0.5 font-mono text-[10px] text-subtle">
        soon
      </kbd>
    </div>
  );
}

export function Topbar({ onOpenMobileNav }: TopbarProps) {
  const location = useLocation();
  const activeItem = findNavItem(location.pathname);
  const section = navigation.find((group) =>
    group.items.some((item) => item.path === activeItem?.path),
  );

  // Keep the mobile drawer state manageable from the topbar button.
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 4);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <header
      className={cn(
        'sticky top-0 z-30 border-b border-border-subtle bg-bg/85 backdrop-blur transition-shadow',
        scrolled && 'shadow-[0_1px_0_0_var(--app-border)]',
      )}
    >
      <div className="flex h-14 items-center gap-3 px-3 sm:px-5">
        <button
          type="button"
          onClick={onOpenMobileNav}
          aria-label="Open navigation"
          className="grid size-9 place-items-center rounded-lg text-muted transition-colors hover:bg-surface-3 hover:text-fg lg:hidden"
        >
          <Menu className="size-5" />
        </button>

        {/* Breadcrumb */}
        <nav aria-label="Breadcrumb" className="hidden min-w-0 items-center gap-1.5 text-[13px] lg:flex">
          {section?.label ? (
            <>
              <span className="text-subtle">{section.label}</span>
              <span className="text-subtle">/</span>
            </>
          ) : null}
          <span className="truncate font-medium text-fg">{activeItem?.label ?? 'Dashboard'}</span>
          {activeItem?.status === 'soon' ? (
            <Badge tone="neutral" size="sm" className="ml-1">
              Phase 2
            </Badge>
          ) : null}
        </nav>

        <SearchField />

        <div className="ml-auto flex items-center gap-1.5 sm:gap-2">
          <ApiStatusPill />
          <ThemeToggle compact />
          <button
            type="button"
            aria-label="Notifications"
            title="Notifications arrive with the campaign phase"
            className="relative grid size-9 place-items-center rounded-lg text-muted transition-colors hover:bg-surface-3 hover:text-fg"
          >
            <Bell className="size-4.5" />
            <span className="absolute top-1.5 right-1.5 size-1.5 rounded-full bg-brand-500" />
          </button>
          <div className="mx-0.5 hidden h-6 w-px bg-border-subtle sm:block" />
          <UserMenu />
        </div>
      </div>
    </header>
  );
}
