/**
 * Campaign + Template contracts (Phase 6).
 *
 * Mirror backend serializers in `apps/campaigns/serializers.py` and
 * `apps/email_engine/serializers.py`.
 */

export type CampaignStatus =
  | 'DRAFT'
  | 'READY'
  | 'RUNNING'
  | 'PAUSED'
  | 'COMPLETED'
  | 'CANCELLED';

export interface Campaign {
  id: number;
  name: string;
  description: string;
  industry: string;
  sub_industry: string;
  location: string;
  minimum_lead_score: number;
  recommended_service: string;
  template: number | null;
  template_name: string;
  template_detail?: EmailTemplate | null;
  scheduled_start_at: string | null;
  scheduled_end_at: string | null;
  sending_start_time: string | null;
  sending_end_time: string | null;
  daily_limit: number;
  status: CampaignStatus;
  status_display: string;
  eligible_count: number;
  audience_size?: number;
  sent_count: number;
  reply_count: number;
  meeting_count: number;
  audience_preview: Record<string, string | number>;
  can_launch: boolean;
  launch_errors: string[];
  progress_pct: number;
  memberships?: number;
  created_at: string;
  updated_at: string;
}

export type CampaignSendStatus = 'PENDING' | 'QUEUED' | 'SENT' | 'REPLIED' | 'BOUNCED' | 'SKIPPED';

export interface CampaignMember {
  id: number;
  lead: number;
  lead_name: string;
  contact_name: string;
  email: string;
  send_status: CampaignSendStatus;
  sent_at: string | null;
  replied_at: string | null;
  created_at: string;
}

export interface EmailTemplate {
  id: number;
  name: string;
  description: string;
  subject: string;
  body: string;
  default_recommended_service: string;
  used_variables: string[];
  unknown_variables: string[];
  missing_variables: string[];
  created_at: string;
  updated_at: string;
}

export interface TemplatePreview {
  subject: string;
  body: string;
  sample: Record<string, string>;
  variables?: string[];
}

export const TEMPLATE_VARIABLES = [
  'first_name',
  'contact_name',
  'company_name',
  'industry',
  'city',
  'state',
  'website',
  'recommended_service',
] as const;

export interface CampaignWizardDraft {
  name: string;
  description: string;
  industry: string;
  sub_industry: string;
  location: string;
  minimum_lead_score: number;
  recommended_service: string;
  template: number | null;
  daily_limit: number;
  scheduled_start_at: string | null;
  scheduled_end_at: string | null;
  sending_start_time: string | null;
  sending_end_time: string | null;
}

export interface CampaignStatusChoice {
  value: CampaignStatus;
  label: string;
  count?: number;
}
