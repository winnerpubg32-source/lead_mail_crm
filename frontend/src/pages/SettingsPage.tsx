import { Building2, Clock, Mail, PlugZap, Send, ShieldCheck } from 'lucide-react';
import { useState } from 'react';

import { PageHeader } from '@/components/layout/PageHeader';
import { ThemeToggle } from '@/components/layout/ThemeToggle';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card, CardBody, CardFooter, CardHeader } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Progress } from '@/components/ui/Progress';
import { Select } from '@/components/ui/Select';
import { Switch } from '@/components/ui/Switch';
import { DAILY_EMAIL_LIMIT } from '@/data/mock/dashboard.mock';
import { useDashboardOverview } from '@/hooks/useDashboardOverview';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { useHealthStatus } from '@/hooks/useHealthStatus';
import { apiUrl } from '@/lib/api/client';
import { env } from '@/lib/env';

function SettingRow({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-3 px-5 py-4">
      <div className="max-w-xl">
        <p className="text-[13.5px] font-medium text-fg">{title}</p>
        <p className="mt-0.5 text-[12.5px] text-muted">{description}</p>
      </div>
      <div className="flex shrink-0 items-center gap-2">{children}</div>
    </div>
  );
}

/**
 * Settings — a small but real surface in Phase 1.
 *
 * Everything that can genuinely work today (theme, local UI preferences, API
 * connectivity diagnostics) is functional; workspace-level persistence is
 * clearly marked as pending the Settings API.
 */
export function SettingsPage() {
  useDocumentTitle('Settings');
  const { data } = useDashboardOverview();
  const health = useHealthStatus();

  const [notifyReplies, setNotifyReplies] = useState(true);
  const [notifyBounces, setNotifyBounces] = useState(true);
  const [pauseOnReply, setPauseOnReply] = useState(true);
  const [dailyLimit, setDailyLimit] = useState(String(DAILY_EMAIL_LIMIT));

  const sent = data?.capacity.sent ?? 0;
  const limit = Number(dailyLimit) || DAILY_EMAIL_LIMIT;
  const usage = limit > 0 ? Math.round((sent / limit) * 100) : 0;

  return (
    <div>
      <PageHeader
        eyebrow="Workspace"
        title="Settings"
        description="Workspace profile, sending limits, notifications and API connectivity. Changes are stored locally until the Settings API ships."
        actions={
          <Badge tone="warning" dot>
            Partially wired
        </Badge>
        }
      />

      <div className="animate-[var(--animate-slide-up)] grid gap-5 xl:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
        <div className="space-y-5">
          <Card>
            <CardHeader
              title="Workspace profile"
              description="Shown on outreach e-mails and reports"
              action={<Building2 className="size-4 text-subtle" />}
            />
            <div className="space-y-3.5 px-5 py-4">
              <label className="block">
                <span className="mb-1.5 block text-[12.5px] font-medium text-muted">Workspace name</span>
                <Input defaultValue="OutreachOS Demo Workspace" disabled />
              </label>
              <div className="grid gap-3.5 sm:grid-cols-2">
                <label className="block">
                  <span className="mb-1.5 block text-[12.5px] font-medium text-muted">
                    Business e-mail
                  </span>
                  <Input defaultValue="outreach@outreachos.app" disabled type="email" />
                </label>
                <label className="block">
                  <span className="mb-1.5 block text-[12.5px] font-medium text-muted">
                    Default state / region
                  </span>
                  <Select defaultValue="TX" disabled>
                    <option value="TX">Texas</option>
                    <option value="CA">California</option>
                    <option value="FL">Florida</option>
                    <option value="NY">New York</option>
                  </Select>
                </label>
              </div>
              <p className="flex items-center gap-1.5 text-[11.5px] text-subtle">
                <ShieldCheck className="size-3.5" />
                Read-only in Phase 1 — the workspace model arrives with the Accounts API.
              </p>
            </div>
          </Card>

          <Card>
            <CardHeader
              title="Outreach &amp; sending limits"
              description="Guard rails enforced by the e-mail engine"
              action={<Send className="size-4 text-subtle" />}
            />
            <div className="divide-y divide-[color:var(--app-border)]">
              <SettingRow
                title="Daily marketing e-mail limit"
                description="Hard cap on marketing sends per day. Defaults to 90 for deliverability."
              >
                <Input
                  type="number"
                  value={dailyLimit}
                  min={1}
                  max={90}
                  onChange={(event) => setDailyLimit(event.target.value)}
                  className="w-24 text-right tabular"
                />
                <span className="text-[12.5px] text-subtle">/ day</span>
              </SettingRow>

              <div className="px-5 py-4">
                <div className="flex items-center justify-between text-[12.5px]">
                  <span className="text-muted">Today’s usage</span>
                  <span className="tabular font-medium text-fg">
                    {sent} / {limit}
                  </span>
                </div>
                <Progress value={usage} className="mt-2" label="Daily sending usage" />
                <p className="mt-2 text-[11.5px] text-subtle">
                  {Math.max(0, limit - sent)} sends remaining today · counts reset at midnight in the
                  workspace timezone.
                </p>
              </div>

              <SettingRow
                title="Sending window"
                description="Marketing e-mails only leave within this window."
              >
                <Input type="time" defaultValue="09:00" disabled className="w-28" />
                <span className="text-[12.5px] text-subtle">to</span>
                <Input type="time" defaultValue="17:00" disabled className="w-28" />
              </SettingRow>

              <SettingRow
                title="Stop sequence on reply"
                description="Immediately cancel remaining steps for a lead that replies."
              >
                <Switch
                  checked={pauseOnReply}
                  onCheckedChange={setPauseOnReply}
                  label="Stop sequence on reply"
                />
              </SettingRow>
            </div>
            <CardFooter>
              <span className="flex items-center gap-1.5">
                <Clock className="size-3.5" />
                Timezone: UTC (configurable per workspace)
              </span>
              <Button variant="primary" size="sm" disabled title="Settings API ships in a later phase">
                Save changes
              </Button>
            </CardFooter>
          </Card>

          <Card>
            <CardHeader
              title="Notifications"
              description="What the workspace alerts you about"
              action={<Mail className="size-4 text-subtle" />}
            />
            <div className="divide-y divide-[color:var(--app-border)]">
              <SettingRow title="Replies" description="Notify me when a lead replies to a sequence.">
                <Switch checked={notifyReplies} onCheckedChange={setNotifyReplies} label="Reply notifications" />
              </SettingRow>
              <SettingRow
                title="Bounces and complaints"
                description="Notify me when deliverability problems are detected."
              >
                <Switch checked={notifyBounces} onCheckedChange={setNotifyBounces} label="Bounce notifications" />
              </SettingRow>
              <SettingRow
                title="Daily summary"
                description="Send a digest of sends, replies and meetings each morning."
              >
                <Switch checked={false} onCheckedChange={() => undefined} disabled label="Daily summary" />
              </SettingRow>
            </div>
          </Card>
        </div>

        <div className="space-y-5">
          <Card>
            <CardHeader title="Appearance" description="Light, dark or follow the system" />
            <CardBody>
              <ThemeToggle />
              <p className="mt-3 text-[11.5px] text-subtle">
                Saved in this browser and applied before first paint — no flash of the wrong theme.
              </p>
            </CardBody>
          </Card>

          <Card>
            <CardHeader
              title="API connectivity"
              description="Live check against the Django backend"
              action={<PlugZap className="size-4 text-subtle" />}
            />
            <CardBody className="space-y-3">
              <div className="flex items-center justify-between text-[12.5px]">
                <span className="text-muted">Data source</span>
                <Badge tone={env.useMockData ? 'warning' : 'brand'} size="sm">
                  {env.useMockData ? 'Placeholder dataset' : 'Django API'}
                </Badge>
              </div>
              <div className="flex items-center justify-between text-[12.5px]">
                <span className="text-muted">Health endpoint</span>
                <Badge tone={health.isSuccess ? 'success' : health.isError ? 'danger' : 'neutral'} size="sm" dot>
                  {health.isSuccess ? 'Reachable' : health.isError ? 'Unreachable' : 'Checking…'}
                </Badge>
              </div>
              <div className="rounded-lg bg-surface-2 px-3 py-2 font-mono text-[11.5px] break-all text-muted ring-1 ring-border-subtle ring-inset">
                GET {apiUrl('health/')}
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => void health.refetch()}
                isLoading={health.isFetching}
                className="w-full"
              >
                Test connection
              </Button>
            </CardBody>
          </Card>

          <Card>
            <CardHeader title="Build phase" description="What is live in this version" />
            <ul className="divide-y divide-[color:var(--app-border)] text-[12.5px]">
              {[
                { label: 'Foundation, routing and design system', done: true },
                { label: 'POSTGRES + REDIS + CELERY infrastructure', done: true },
                { label: 'Health endpoint &amp; basic authentication', done: true },
                { label: 'Dashboard with placeholder metrics', done: true },
                { label: 'Imports, campaigns, SMTP, AI and CRM logic', done: false },
              ].map((item) => (
                <li key={item.label} className="flex items-center justify-between gap-3 px-5 py-2.5">
                  <span className="text-muted" dangerouslySetInnerHTML={{ __html: item.label }} />
                  <Badge tone={item.done ? 'success' : 'neutral'} size="sm">
                    {item.done ? 'Done' : 'Phase 2'}
                  </Badge>
                </li>
              ))}
            </ul>
          </Card>
        </div>
      </div>
    </div>
  );
}
