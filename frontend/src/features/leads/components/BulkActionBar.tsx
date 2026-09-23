import { Download, Megaphone, UserMinus } from 'lucide-react';
import { useState } from 'react';

import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Select } from '@/components/ui/Select';
import { useBulkAction, useExportLeads } from '@/hooks/useLeads';
import { toast } from '@/lib/utils/toast';
import type { LeadStatus, ListParams } from '@/types/lead';
import { leadStatusConfig } from '@/config/status';

interface Props {
  selected: Set<number>;
  onClear: () => void;
  params: ListParams;
}

export function BulkActionBar({ selected, onClear, params }: Props) {
  const bulk = useBulkAction();
  const exporter = useExportLeads();
  const [industry, setIndustry] = useState('');
  const [status, setStatus] = useState<LeadStatus | ''>('');
  const [campaign, setCampaign] = useState('');

  const count = selected.size;
  if (count === 0) return null;

  const ids = Array.from(selected);

  const run = (payload: Parameters<typeof bulk.mutate>[0]) => {
    bulk.mutate(payload, {
      onSuccess: (res) => {
        toast.success(`${res.affected} lead(s) updated`);
        onClear();
      },
      onError: (err: Error) => toast.error(err.message || 'Bulk action failed'),
    });
  };

  const handleExport = () => {
    exporter.mutate({ ...params, id__in: ids.join(',') }, {
      onSuccess: () => toast.success('Export started'),
      onError: (err: Error) => toast.error(err.message || 'Export failed'),
    });
  };

  return (
    <div className="flex flex-wrap items-center gap-2 border-t border-border-subtle bg-surface-2/80 px-3 py-2">
      <Badge tone="brand" size="sm">{count} selected</Badge>

      <Select
        value={status}
        onChange={(e) => {
          const value = e.target.value as LeadStatus | '';
          setStatus(value);
          if (value) run({ ids, action: 'change_status', lead_status: value });
        }}
        className="h-8 text-[12px]"
      >
        <option value="">Change status…</option>
        {Object.entries(leadStatusConfig).map(([value, cfg]) => (
          <option key={value} value={value}>
            {cfg.label}
          </option>
        ))}
      </Select>

      <div className="flex items-center gap-1">
        <input
          type="text"
          value={industry}
          onChange={(e) => setIndustry(e.target.value)}
          placeholder="Set industry…"
          className="h-8 w-44 rounded-md border border-border-subtle bg-surface-1 px-2 text-[12px] outline-none focus:ring-2 focus:ring-brand-500/30"
        />
        <Button
          size="sm"
          variant="outline"
          disabled={!industry.trim()}
          onClick={() => run({ ids, action: 'change_industry', industry: industry.trim() })}
          isLoading={bulk.isPending}
        >
          Set
        </Button>
      </div>

      <div className="flex items-center gap-1">
        <input
          type="text"
          value={campaign}
          onChange={(e) => setCampaign(e.target.value)}
          placeholder="Assign campaign…"
          className="h-8 w-44 rounded-md border border-border-subtle bg-surface-1 px-2 text-[12px] outline-none focus:ring-2 focus:ring-brand-500/30"
        />
        <Button
          size="sm"
          variant="outline"
          disabled={!campaign.trim()}
          leadingIcon={<Megaphone className="size-3" />}
          onClick={() => run({ ids, action: 'assign_campaign', campaign_name: campaign.trim() })}
          isLoading={bulk.isPending}
        >
          Assign
        </Button>
      </div>

      <Button
        size="sm"
        variant="danger"
        leadingIcon={<UserMinus className="size-3" />}
        onClick={() => {
          if (confirm(`Suppress ${count} lead(s)? This sets status to DO_NOT_CONTACT.`)) {
            run({ ids, action: 'suppress' });
          }
        }}
        isLoading={bulk.isPending}
      >
        Suppress
      </Button>

      <Button
        size="sm"
        variant="outline"
        leadingIcon={<Download className="size-3" />}
        onClick={handleExport}
        isLoading={exporter.isPending}
      >
        Export CSV
      </Button>

      <div className="ml-auto">
        <Button size="sm" variant="ghost" onClick={onClear}>
          Clear selection
        </Button>
      </div>
    </div>
  );
}
