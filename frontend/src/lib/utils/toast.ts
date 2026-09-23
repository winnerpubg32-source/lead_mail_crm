/**
 * Lightweight toast helper.
 *
 * A single notification container is appended to <body> on first use. Success
 * and error toasts auto-dismiss after a few seconds. This is intentionally
 * minimal — a design-system toast component arrives later if needed.
 */

import { cn } from '@/lib/utils/cn';

type Tone = 'success' | 'error' | 'info';

interface ToastOptions {
  title: string;
  description?: string;
  tone?: Tone;
  duration?: number;
}

interface ToastHandle {
  dismiss: () => void;
}

let container: HTMLDivElement | null = null;

function ensureContainer() {
  if (container) return container;
  container = document.createElement('div');
  container.className =
    'pointer-events-none fixed right-4 bottom-4 z-50 flex w-[320px] flex-col gap-2';
  document.body.appendChild(container);
  return container;
}

export function toast({ title, description, tone = 'info', duration = 3500 }: ToastOptions): ToastHandle {
  const root = ensureContainer();
  const el = document.createElement('div');
  el.setAttribute('role', 'status');
  el.className = cn(
    'pointer-events-auto rounded-lg border px-4 py-3 text-sm shadow-lg transition-all',
    tone === 'success' && 'border-emerald-200 bg-emerald-50 text-emerald-900 dark:bg-emerald-500/15 dark:text-emerald-100 dark:border-emerald-500/30',
    tone === 'error' && 'border-rose-200 bg-rose-50 text-rose-900 dark:bg-rose-500/15 dark:text-rose-100 dark:border-rose-500/30',
    tone === 'info' && 'border-slate-200 bg-surface text-fg',
  );
  const titleEl = document.createElement('div');
  titleEl.className = 'font-medium';
  titleEl.textContent = title;
  el.appendChild(titleEl);
  if (description) {
    const desc = document.createElement('div');
    desc.className = 'mt-0.5 text-[12.5px] opacity-80';
    desc.textContent = description;
    el.appendChild(desc);
  }
  root.appendChild(el);
  const timer = window.setTimeout(() => dismiss(), duration);

  function dismiss() {
    window.clearTimeout(timer);
    el.style.opacity = '0';
    el.style.transform = 'translateY(8px)';
    el.style.transition = 'all 200ms';
    window.setTimeout(() => {
      if (el.parentNode) el.parentNode.removeChild(el);
    }, 200);
  }

  return { dismiss };
}
