import { ChevronDown, LogOut, Settings, UserCircle2 } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';

import { Avatar } from '@/components/ui/Avatar';
import { cn } from '@/lib/utils/cn';

/** Placeholder operator profile — replaced by `GET /api/v1/accounts/me/` later. */
const currentUser = {
  name: 'Ava Bennett',
  email: 'ava@outreachos.app',
  role: 'Workspace owner',
};

export function UserMenu() {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onPointerDown = (event: MouseEvent) => {
      if (!containerRef.current?.contains(event.target as Node)) setOpen(false);
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false);
    };
    document.addEventListener('mousedown', onPointerDown);
    document.addEventListener('keydown', onKeyDown);
    return () => {
      document.removeEventListener('mousedown', onPointerDown);
      document.removeEventListener('keydown', onKeyDown);
    };
  }, [open]);

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-haspopup="menu"
        aria-expanded={open}
        className="flex items-center gap-2 rounded-lg py-1 pr-2 pl-1 transition-colors hover:bg-surface-3"
      >
        <Avatar name={currentUser.name} size="md" />
        <span className="hidden text-left leading-tight sm:block">
          <span className="block text-[13px] font-medium text-fg">{currentUser.name}</span>
          <span className="block text-[11px] text-subtle">{currentUser.role}</span>
        </span>
        <ChevronDown className={cn('size-3.5 text-subtle transition-transform', open && 'rotate-180')} />
      </button>

      {open ? (
        <div
          role="menu"
          className="animate-[var(--animate-fade-in)] absolute right-0 z-50 mt-2 w-60 overflow-hidden rounded-xl border border-border-subtle bg-surface shadow-xl"
        >
          <div className="border-b border-border-subtle px-3.5 py-3">
            <p className="text-[13px] font-medium text-fg">{currentUser.name}</p>
            <p className="truncate text-[12px] text-muted">{currentUser.email}</p>
          </div>
          <div className="p-1.5">
            <Link
              to="/settings"
              role="menuitem"
              onClick={() => setOpen(false)}
              className="flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-[13px] text-fg transition-colors hover:bg-surface-3"
            >
              <UserCircle2 className="size-4 text-subtle" />
              Profile
            </Link>
            <Link
              to="/settings"
              role="menuitem"
              onClick={() => setOpen(false)}
              className="flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-[13px] text-fg transition-colors hover:bg-surface-3"
            >
              <Settings className="size-4 text-subtle" />
              Workspace settings
            </Link>
          </div>
          <div className="border-t border-border-subtle p-1.5">
            <button
              type="button"
              role="menuitem"
              disabled
              title="Authentication ships in a later phase"
              className="flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-[13px] text-subtle"
            >
              <LogOut className="size-4" />
              Sign out (later phase)
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
