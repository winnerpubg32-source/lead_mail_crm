import { Suspense, lazy } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';

import { AppShell } from '@/components/layout/AppShell';
import { DashboardSkeleton } from '@/features/dashboard/components/DashboardSkeleton';
import { LoadingState } from '@/components/feedback/LoadingState';
import { paths } from '@/routes/paths';

/**
 * Route table with code-split pages.
 *
 * `/dashboard` is the only fully functional page in Phase 1; every other module
 * renders the shared placeholder driven by `config/modules.ts`. Each page is
 * lazily imported so the initial bundle only carries the shell + dashboard.
 */
const DashboardPage = lazy(() =>
  import('@/pages/DashboardPage').then((module) => ({ default: module.DashboardPage })),
);
const SettingsPage = lazy(() =>
  import('@/pages/SettingsPage').then((module) => ({ default: module.SettingsPage })),
);
const ModulePage = lazy(() =>
  import('@/pages/ModulePlaceholderPage').then((module) => ({ default: module.ModulePage })),
);
const NotFoundPage = lazy(() =>
  import('@/pages/NotFoundPage').then((module) => ({ default: module.NotFoundPage })),
);

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<Navigate to={paths.dashboard} replace />} />
        <Route
          path={paths.dashboard}
          element={
            <Suspense fallback={<DashboardSkeleton />}>
              <DashboardPage />
            </Suspense>
          }
        />

        {/* Phase 2 modules — each renders the shared placeholder */}
        {(
          [
            [paths.leads, 'leads'],
            [paths.companies, 'companies'],
            [paths.contacts, 'contacts'],
            [paths.imports, 'imports'],
            [paths.campaigns, 'campaigns'],
            [paths.email, 'email'],
            [paths.followUps, 'follow-ups'],
            [paths.crm, 'crm'],
            [paths.analytics, 'analytics'],
            [paths.templates, 'templates'],
            [paths.ai, 'ai'],
            [paths.suppression, 'suppression'],
          ] as const
        ).map(([path, moduleKey]) => (
          <Route
            key={path}
            path={path}
            element={
              <Suspense fallback={<LoadingState label="Loading module…" />}>
                <ModulePage moduleKey={moduleKey} />
              </Suspense>
            }
          />
        ))}

        {/* Workspace — real (small) settings surface */}
        <Route
          path={paths.settings}
          element={
            <Suspense fallback={<LoadingState label="Loading settings…" />}>
              <SettingsPage />
            </Suspense>
          }
        />

        <Route
          path="*"
          element={
            <Suspense fallback={<LoadingState />}>
              <NotFoundPage />
            </Suspense>
          }
        />
      </Route>
    </Routes>
  );
}
