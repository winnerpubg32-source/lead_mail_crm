import { Building2, Globe, Link as LinkIcon, Mail, MapPin, Phone, User } from 'lucide-react';

import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { emailStatusConfig, leadStatusConfig, scoreClassificationConfig } from '@/config/status';
import { sourceLabel } from '@/config/list-options';
import { cn } from '@/lib/utils/cn';
import type { LeadDetail } from '@/types/lead';

interface Props {
  lead: LeadDetail;
}

export function ContactCard({ lead }: Props) {
  const code = lead.score_classification ?? 'UNQUALIFIED';
  const scoreCfg = scoreClassificationConfig[code];

  return (
    <Card className="overflow-hidden">
      <div className="flex items-start gap-4 border-b border-border-subtle p-5">
        <div className="grid size-12 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/10 dark:text-brand-300">
          <Building2 className="size-6" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="truncate text-lg font-semibold text-fg">{lead.company_name || 'Unassigned'}</h2>
            <Badge tone={scoreCfg.tone} size="sm">{scoreCfg.label} · {lead.lead_score}</Badge>
          </div>
          <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-[12.5px] text-muted">
            {lead.industry && <span>{lead.industry}{lead.sub_industry ? ` · ${lead.sub_industry}` : ''}</span>}
            {(lead.city || lead.state) && (
              <span className="inline-flex items-center gap-1">
                <MapPin className="size-3 text-subtle" />
                {[lead.city, lead.state, lead.country].filter(Boolean).join(', ')}
              </span>
            )}
            {lead.website && (
              <a
                href={lead.website}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 text-brand-600 hover:underline dark:text-brand-300"
              >
                <Globe className="size-3" />
                {lead.website_domain || lead.website}
              </a>
            )}
            <span className="inline-flex items-center gap-1">
              <LinkIcon className="size-3 text-subtle" />
              Source: {lead.source ? sourceLabel(lead.source) : '—'}
            </span>
          </div>
          <div className="mt-2 flex flex-wrap gap-1.5">
            <Badge tone={leadStatusConfig[lead.lead_status].tone} size="sm" dot>
              {leadStatusConfig[lead.lead_status].label}
            </Badge>
            <Badge tone={emailStatusConfig[lead.email_status].tone} size="sm">
              {emailStatusConfig[lead.email_status].label}
            </Badge>
            {!lead.is_contactable && (
              <Badge tone="danger" size="sm">Not contactable</Badge>
            )}
          </div>
        </div>
      </div>
      <div className="grid grid-cols-1 gap-4 p-5 md:grid-cols-2">
        <InfoRow icon={<User className="size-4" />} label="Contact">
          {lead.contact_name ? (
            <>
              <span className="font-medium text-fg">{lead.contact_name}</span>
              {lead.job_title && <span className="text-subtle"> · {lead.job_title}</span>}
            </>
          ) : (
            <span className="text-subtle">No contact assigned</span>
          )}
        </InfoRow>
        <InfoRow icon={<Mail className="size-4" />} label="E-mail">
          {lead.email ? (
            <a href={`mailto:${lead.email}`} className="font-mono text-[12.5px] text-brand-600 hover:underline">
              {lead.email}
            </a>
          ) : (
            <span className="text-subtle">—</span>
          )}
        </InfoRow>
        <InfoRow icon={<Phone className="size-4" />} label="Phone">
          {lead.phone ? (
            <a href={`tel:${lead.phone}`} className="text-[12.5px] text-muted hover:text-brand-600">
              {lead.phone}
            </a>
          ) : (
            <span className="text-subtle">—</span>
          )}
        </InfoRow>
        <InfoRow icon={<Globe className="size-4" />} label="Website">
          {lead.website ? (
            <a
              href={lead.website}
              target="_blank"
              rel="noreferrer"
              className="truncate text-[12.5px] text-brand-600 hover:underline"
            >
              {lead.website}
            </a>
          ) : (
            <span className="text-subtle">—</span>
          )}
        </InfoRow>
        <InfoRow icon={<MapPin className="size-4" />} label="Address" className="md:col-span-2">
          {[lead.street_address, lead.city, lead.state, lead.zip_code, lead.country]
            .filter(Boolean)
            .join(', ') || <span className="text-subtle">No address on file</span>}
        </InfoRow>
      </div>
    </Card>
  );
}

function InfoRow({
  icon,
  label,
  children,
  className,
}: {
  icon: React.ReactNode;
  label: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn('flex items-start gap-3', className)}>
      <span className="mt-0.5 grid size-7 shrink-0 place-items-center rounded-md bg-surface-2 text-subtle">
        {icon}
      </span>
      <div className="min-w-0">
        <p className="text-[11px] font-medium uppercase tracking-wide text-subtle">{label}</p>
        <div className="text-[13px] text-fg">{children}</div>
      </div>
    </div>
  );
}
