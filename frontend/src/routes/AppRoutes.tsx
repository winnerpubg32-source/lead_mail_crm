import { Suspense, lazy } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';

import { AppShell } from '@/components/layout/AppShell';
import { DashboardSkeleton } from '@/features/dashboard/components/DashboardSkeleton';
import { LoadingState } from '@/components/feedback/LoadingState';
import { TablePageSkeleton } from '@/features/leads/components/TablePageSkeleton';
import { paths } from '@/routes/paths';

/**
 * Route table with code-split pages.
 *
 * Phase 3: `/imports` (upload, mapping, preview, progress) and
 * `/imports/history` are real, API-backed screens.
 *
 * Phase 2: `/leads`, `/companies` and `/contacts` are real, API-backed tables.
 * `/dashboard` is backed by the analytics endpoint (placeholder dataset until
 * that endpoint exists), and the remaining modules render the shared placeholder
 * driven by `config/modules.ts`. Every page is lazily imported so the initial
 * bundle only carries the shell + dashboard.
 */
const DashboardPage = lazy(() =>
  import('@/pages/DashboardPage').then((module) => ({ default: module.DashboardPage })),
);
const SettingsPage = lazy(() =>
  import('@/pages/SettingsPage').then((module) => ({ default: module.SettingsPage })),
);
const LeadsPage = lazy(() =>
  import('@/pages/LeadsPage').then((module) => ({ default: module.LeadsPage })),
);
const CompaniesPage = lazy(() =>
  import('@/pages/CompaniesPage').then((module) => ({ default: module.CompaniesPage })),
);
const ContactsPage = lazy(() =>
  import('@/pages/ContactsPage').then((module) => ({ default: module.ContactsPage })),
);
const ImportsPage = lazy(() =>
  import('@/pages/ImportsPage').then((module) => ({ default: module.ImportsPage })),
);
const ImportHistoryPage = lazy(() =>
  import('@/pages/ImportHistoryPage').then((module) => ({ default: module.ImportHistoryPage })),
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

        {/* Lead database — implemented (Phase 2) */}
        <Route
          path={paths.leads}
          element={
            <Suspense fallback={<TablePageSkeleton />}>
              <LeadsPage />
            </Suspense>
          }
        />
        <Route
          path={paths.companies}
          element={
            <Suspense fallback={<TablePageSkeleton />}>
              <CompaniesPage />
            </Suspense>
          }
        />
        <Route
          path={paths.contacts}
          element={
            <Suspense fallback={<TablePageSkeleton />}>
              <ContactsPage />
            </Suspense>
          }
        />

        {/* Imports — implemented (Phase 3) */}
        <Route
          path={paths.imports}
          element={
            <Suspense fallback={<TablePageSkeleton />}>
              <ImportsPage />
            </Suspense>
          }
        />
        <Route
          path={paths.importsHistory}
          element={
            <Suspense fallback={<TablePageSkeleton />}>
              <ImportHistoryPage />
            </Suspense>
          }
        />

        {/* Later-phase modules — each renders the shared placeholder */}
        {(
          [
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
