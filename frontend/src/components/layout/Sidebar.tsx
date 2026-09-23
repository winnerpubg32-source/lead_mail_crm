import { ChevronLeft, PanelLeft, Send, X } from 'lucide-react';
import { NavLink } from 'react-router-dom';

import { Brand } from '@/components/layout/Brand';
import { Badge } from '@/components/ui/Badge';
import { navigation, type NavItem } from '@/config/navigation';
import { cn } from '@/lib/utils/cn';

export interface SidebarProps {
  collapsed: boolean;
  onToggleCollapsed: () => void;
  /** Mobile drawer state (ignored on desktop). */
  mobileOpen: boolean;
  onCloseMobile: () => void;
  dailySent: number;
  dailyLimit: number;
}

function NavItemLink({
  item,
  collapsed,
  onNavigate,
}: {
  item: NavItem;
  collapsed: boolean;
  onNavigate?: () => void;
}) {
  const Icon = item.icon;
  return (
    <NavLink
      to={item.path}
      onClick={onNavigate}
      title={collapsed ? item.label : undefined}
      className={({ isActive }) =>
        cn(
          'group relative flex items-center gap-2.5 rounded-lg text-[13.5px] font-medium transition-colors',
          collapsed ? 'justify-center px-0 py-2.5' : 'px-2.5 py-2',
          isActive
            ? 'bg-sidebar-active text-sidebar-active-fg'
            : 'text-sidebar-fg hover:bg-surface-3 hover:text-fg',
        )
      }
    >
      {({ isActive }) => (
        <>
          <Icon
            className={cn('size-4.5 shrink-0', isActive ? 'text-brand-600 dark:text-brand-300' : 'text-subtle')}
          />
          {!collapsed ? (
            <>
              <span className="flex-1 truncate">{item.label}</span>
              {item.status === 'soon' ? (
                <span className="size-1.5 shrink-0 rounded-full bg-border-strong" aria-hidden="true" />
              ) : null}
            </>
          ) : null}
        </>
      )}
    </NavLink>
  );
}

/** Primary navigation — responsive: fixed rail on desktop, drawer on mobile. */
export function Sidebar({
  collapsed,
  onToggleCollapsed,
  mobileOpen,
  onCloseMobile,
  dailySent,
  dailyLimit,
}: SidebarProps) {
  const usage = dailyLimit > 0 ? Math.min(100, Math.round((dailySent / dailyLimit) * 100)) : 0;

  const content = (
    <div className="flex h-full flex-col gap-1 border-r border-sidebar-border bg-sidebar">
      {/* Brand + collapse control */}
      <div className={cn('flex items-center gap-2 px-3 py-3.5', collapsed && 'justify-center px-2')}>
        <Brand collapsed={collapsed} />
        <div className="ml-auto flex items-center gap-1">
          <button
            type="button"
            onClick={onToggleCollapsed}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            className="hidden size-7 place-items-center rounded-md text-subtle transition-colors hover:bg-surface-3 hover:text-fg lg:grid"
          >
            {collapsed ? <PanelLeft className="size-4" /> : <ChevronLeft className="size-4" />}
          </button>
          <button
            type="button"
            onClick={onCloseMobile}
            aria-label="Close navigation"
            className="grid size-7 place-items-center rounded-md text-subtle transition-colors hover:bg-surface-3 hover:text-fg lg:hidden"
          >
            <X className="size-4" />
          </button>
        </div>
      </div>

      {/* Navigation */}
      <nav aria-label="Main navigation" className="scrollbar-thin flex-1 space-y-4 overflow-y-auto px-2.5 pb-4">
        {navigation.map((section) => (
          <div key={section.id}>
            {section.label && !collapsed ? (
              <p className="px-2.5 pb-1.5 text-[10.5px] font-semibold tracking-wider text-subtle uppercase">
                {section.label}
              </p>
            ) : null}
            {section.label && collapsed ? (
              <div className="mx-auto mb-2 h-px w-6 bg-sidebar-border" aria-hidden="true" />
            ) : null}
            <div className="space-y-0.5">
              {section.items.map((item) => (
                <NavItemLink key={item.path} item={item} collapsed={collapsed} onNavigate={onCloseMobile} />
              ))}
            </div>
          </div>
        ))}
      </nav>

      {/* Daily capacity mini-widget */}
      <div className={cn('border-t border-sidebar-border p-3', collapsed && 'px-2')}>
        {collapsed ? (
          <div
            className="grid place-items-center rounded-lg bg-surface-3 py-2"
            title={`Daily capacity ${dailySent}/${dailyLimit}`}
          >
            <Send className="size-4 text-subtle" />
          </div>
        ) : (
          <div className="rounded-lg bg-surface-2 p-3 ring-1 ring-border-subtle ring-inset">
            <div className="flex items-center justify-between">
              <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold tracking-wide text-subtle uppercase">
                <Send className="size-3" />
                Daily capacity
              </span>
              <Badge tone="brand" size="sm">
                {usage}%
              </Badge>
            </div>
            <p className="tabular mt-2 text-[13px] text-fg">
              <span className="font-semibold">{dailySent}</span>
              <span className="text-subtle"> / {dailyLimit} sent</span>
            </p>
            <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-surface-3">
              <div className="h-full rounded-full bg-brand-500" style={{ width: `${usage}%` }} />
            </div>
            <p className="mt-2 text-[11.5px] text-subtle">
              {Math.max(0, dailyLimit - dailySent)} sends remaining today
            </p>
          </div>
        )}
        {!collapsed ? (
          <p className="mt-2.5 text-center text-[10.5px] text-subtle">
            Phase 1 · foundation build v0.1.0
          </p>
        ) : null}
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop rail */}
      <aside
        className={cn(
          'sticky top-0 hidden h-dvh shrink-0 transition-[width] duration-200 lg:block',
          collapsed ? 'w-[76px]' : 'w-[264px]',
        )}
      >
        {content}
      </aside>

      {/* Mobile drawer */}
      <div
        className={cn(
          'fixed inset-0 z-50 lg:hidden',
          mobileOpen ? 'pointer-events-auto' : 'pointer-events-none',
        )}
        aria-hidden={!mobileOpen}
      >
        <div
          onClick={onCloseMobile}
          className={cn(
            'absolute inset-0 bg-overlay transition-opacity duration-200',
            mobileOpen ? 'opacity-100' : 'opacity-0',
          )}
        />
        <div
          className={cn(
            'absolute inset-y-0 left-0 w-[264px] shadow-xl transition-transform duration-250 ease-out',
            mobileOpen ? 'translate-x-0' : '-translate-x-full',
          )}
        >
          {content}
        </div>
      </div>
    </>
  );
}
