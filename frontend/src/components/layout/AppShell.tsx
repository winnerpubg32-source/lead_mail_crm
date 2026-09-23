import { useState } from 'react';
import { Outlet } from 'react-router-dom';

import { Sidebar } from '@/components/layout/Sidebar';
import { Topbar } from '@/components/layout/Topbar';
import { DAILY_EMAIL_LIMIT } from '@/data/mock/dashboard.mock';
import { useDashboardOverview } from '@/hooks/useDashboardOverview';
import { useIsTablet } from '@/hooks/useMediaQuery';
import { useLocalStorage } from '@/hooks/useLocalStorage';

/**
 * Application frame: responsive sidebar + topbar + routed page content.
 *
 * The shell also feeds the sidebar's "daily capacity" widget from the same
 * dashboard query the page uses (React Query de-duplicates the request).
 */
export function AppShell() {
  const [collapsed, setCollapsed] = useLocalStorage('outreachos.sidebar-collapsed', false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const isTablet = useIsTablet();
  const { data } = useDashboardOverview();

  const sent = data?.capacity.sent ?? 0;
  const limit = data?.capacity.limit ?? DAILY_EMAIL_LIMIT;

  // The drawer only exists below the tablet breakpoint: deriving this avoids
  // state synchronisation effects. Navigation closes it via the sidebar's
  // onNavigate handler.
  const drawerOpen = mobileOpen && isTablet;

  return (
    <div className="flex min-h-dvh bg-bg">
      <Sidebar
        collapsed={collapsed}
        onToggleCollapsed={() => setCollapsed((value) => !value)}
        mobileOpen={drawerOpen}
        onCloseMobile={() => setMobileOpen(false)}
        dailySent={sent}
        dailyLimit={limit}
      />

      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar onOpenMobileNav={() => setMobileOpen(true)} />
        <main className="flex-1 px-3 py-5 sm:px-5 lg:px-7">
          <div className="mx-auto w-full max-w-[1600px]">
            <Outlet />
          </div>
        </main>
        <footer className="border-t border-border-subtle px-5 py-4 text-[12px] text-subtle">
          <div className="mx-auto flex max-w-[1600px] flex-wrap items-center justify-between gap-2">
            <span>OutreachOS · Phase 1 foundation</span>
            <span>
              Marketing e-mail limit: <span className="tabular font-medium text-muted">{limit}/day</span>
            </span>
          </div>
        </footer>
      </div>
    </div>
  );
}
