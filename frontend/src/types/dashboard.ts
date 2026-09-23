/**
 * Dashboard domain types.
 *
 * IMPORTANT (Phase 1): these interfaces are the contract between the UI and the
 * data layer. They are intentionally written as the shape Django REST Framework
 * will return from `GET /api/v1/analytics/dashboard/`, so switching from the
 * mock data source to the live API requires no component changes.
 *
 * See `src/services/dashboard.service.ts` for the single switch point.
 */

export type MetricTone = 'brand' | 'emerald' | 'amber' | 'violet' | 'sky' | 'rose';

export type TrendDirection = 'up' | 'down' | 'flat';

export interface MetricTrend {
  /** Percentage change versus the previous comparison period. */
  value: number;
  direction: TrendDirection;
  /** Whether an increase is good news (some metrics invert this). */
  positive: boolean;
  /** Human readable comparison window, e.g. "vs. last week". */
  label: string;
}

export interface MetricCardData {
  id: string;
  label: string;
  value: number;
  /** Pre-formatted value so the UI never has to guess the unit. */
  displayValue: string;
  unit?: 'count' | 'percent' | 'currency';
  trend?: MetricTrend;
  /** Last 7 periods, oldest first — rendered as a sparkline. */
  sparkline?: number[];
  tone: MetricTone;
  hint?: string;
}

// Lead/email statuses come from the API contract so the dashboard, the lead
// table and Django all speak one vocabulary (see types/lead.ts).
import type { EmailStatus, LeadStatus } from './lead';

export type { EmailStatus, LeadStatus };

export interface LeadRow {
  id: string;
  companyName: string;
  contactName: string;
  email: string;
  jobTitle: string;
  industry: string;
  city: string;
  state: string;
  website: string;
  status: LeadStatus;
  emailStatus: EmailStatus;
  /** 0–100 qualification score computed by the lead engine (later phase). */
  score: number;
  source: string;
  createdAt: string;
}

export interface DailyCapacityData {
  /** Marketing e-mails already sent today. */
  sent: number;
  /** Product guard rail: 90 marketing e-mails per day. */
  limit: number;
  remaining: number;
  queued: number;
  failed: number;
  /** Sending window currently configured for the workspace. */
  windowLabel: string;
  /** Sends per hour for the last 8 hours — drives the mini bar chart. */
  hourly: Array<{ hour: string; sent: number }>;
}

export type OutreachEventType = 'sent' | 'queued' | 'reply' | 'bounce' | 'meeting' | 'unsubscribe';

export interface OutreachEvent {
  id: string;
  type: OutreachEventType;
  companyName: string;
  contactName: string;
  subject: string;
  campaignName: string;
  occurredAt: string;
}

export interface LeadSourceBreakdown {
  id: string;
  label: string;
  count: number;
  /** 0–100 share of total leads. */
  share: number;
  color: string;
}

export type CampaignStatus = 'draft' | 'scheduled' | 'active' | 'paused' | 'completed';

export interface CampaignSummary {
  id: string;
  name: string;
  status: CampaignStatus;
  audience: number;
  sent: number;
  replies: number;
  meetings: number;
  /** 0–100 completion against the audience size. */
  progress: number;
  replyRate: number;
  endsAt: string;
}

export interface PipelineStage {
  id: string;
  label: string;
  count: number;
  /** Weighted value in USD. */
  value: number;
  /** Share of leads that reached this stage (0–100). */
  conversion: number;
  tone: MetricTone;
}

export interface DashboardOverview {
  /** When the payload was produced — shown in the dashboard header. */
  generatedAt: string;
  metrics: MetricCardData[];
  capacity: DailyCapacityData;
  todaysOutreach: OutreachEvent[];
  recentLeads: LeadRow[];
  leadSources: LeadSourceBreakdown[];
  campaigns: CampaignSummary[];
  pipeline: PipelineStage[];
}
