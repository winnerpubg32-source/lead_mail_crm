/**
 * Placeholder dashboard dataset.
 *
 * ⚠️ UI DEVELOPMENT ONLY. Every number below is fabricated so the dashboard can
 * be designed and reviewed before the outreach engine exists. Nothing here is
 * sent, stored or synced anywhere.
 *
 * Replacing it: set `VITE_USE_MOCK_DATA=false` and implement the Django endpoint
 * `GET /api/v1/analytics/dashboard/` returning the `DashboardOverview` shape
 * (see `src/types/dashboard.ts`). No component touches this module directly —
 * everything goes through `src/services/dashboard.service.ts`.
 */

import { chartPalette, sourceSeriesColors } from '@/config/chart-colors';
import type {
  CampaignSummary,
  DailyCapacityData,
  DashboardOverview,
  LeadRow,
  LeadSourceBreakdown,
  MetricCardData,
  OutreachEvent,
  PipelineStage,
} from '@/types/dashboard';

import { formatCompactNumber, formatCurrency, formatNumber } from '@/lib/utils/format';

/** Product guard rail from the brief: at most 90 marketing e-mails per day. */
export const DAILY_EMAIL_LIMIT = 90;

const HOUR = 60 * 60 * 1000;
const DAY = 24 * HOUR;

function isoOffset(msFromNow: number): string {
  return new Date(Date.now() - msFromNow).toISOString();
}

function isoInFuture(msFromNow: number): string {
  return new Date(Date.now() + msFromNow).toISOString();
}

/* -------------------------------------------------------------------------- */
/* Top metric cards                                                           */
/* -------------------------------------------------------------------------- */

function buildMetrics(capacity: DailyCapacityData): MetricCardData[] {
  return [
    {
      id: 'total-leads',
      label: 'Total Leads',
      value: 28490,
      displayValue: formatNumber(28490),
      unit: 'count',
      tone: 'brand',
      trend: { value: 8.4, direction: 'up', positive: true, label: 'vs. last week' },
      sparkline: [21200, 22050, 23100, 24080, 25300, 26900, 28490],
      hint: 'All leads in the workspace',
    },
    {
      id: 'valid-emails',
      label: 'Valid Emails',
      value: 24318,
      displayValue: formatNumber(24318),
      unit: 'count',
      tone: 'sky',
      trend: { value: 3.1, direction: 'up', positive: true, label: 'vs. last week' },
      sparkline: [18900, 19600, 20400, 21800, 22900, 23600, 24318],
      hint: '85.4% of the lead database',
    },
    {
      id: 'qualified-leads',
      label: 'Qualified Leads',
      value: 5612,
      displayValue: formatNumber(5612),
      unit: 'count',
      tone: 'violet',
      trend: { value: 12.7, direction: 'up', positive: true, label: 'vs. last week' },
      sparkline: [3980, 4230, 4520, 4790, 5120, 5390, 5612],
      hint: 'Fit + intent score threshold met',
    },
    {
      id: 'emails-sent-today',
      label: 'Emails Sent Today',
      value: capacity.sent,
      displayValue: formatNumber(capacity.sent),
      unit: 'count',
      tone: 'emerald',
      trend: { value: 4.2, direction: 'up', positive: true, label: 'vs. yesterday' },
      sparkline: capacity.hourly.map((point) => point.sent),
      hint: `${formatNumber(capacity.queued)} queued for the next sending window`,
    },
    {
      id: 'daily-capacity',
      label: 'Daily Capacity',
      value: capacity.limit,
      displayValue: `${capacity.sent} / ${capacity.limit}`,
      unit: 'count',
      tone: 'amber',
      trend: {
        value: capacity.limit === 0 ? 0 : Math.round((capacity.sent / capacity.limit) * 1000) / 10,
        direction: 'flat',
        positive: true,
        label: 'of today’s limit used',
      },
      hint: `${formatNumber(capacity.remaining)} sends remaining today`,
    },
    {
      id: 'replies',
      label: 'Replies',
      value: 412,
      displayValue: formatNumber(412),
      unit: 'count',
      tone: 'emerald',
      trend: { value: 6.8, direction: 'up', positive: true, label: 'vs. last week' },
      sparkline: [198, 224, 260, 289, 331, 372, 412],
      hint: 'Across all active campaigns',
    },
    {
      id: 'meetings',
      label: 'Meetings',
      value: 87,
      displayValue: formatNumber(87),
      unit: 'count',
      tone: 'sky',
      trend: { value: 9.5, direction: 'up', positive: true, label: 'vs. last week' },
      sparkline: [34, 41, 48, 58, 66, 76, 87],
      hint: 'Booked from replies this month',
    },
    {
      id: 'opportunities',
      label: 'Opportunities',
      value: 46,
      displayValue: formatNumber(46),
      unit: 'count',
      tone: 'rose',
      trend: { value: 2.2, direction: 'down', positive: false, label: 'vs. last week' },
      sparkline: [22, 29, 33, 38, 44, 48, 46],
      hint: `${formatCurrency(486000)} open pipeline value`,
    },
  ];
}

/* -------------------------------------------------------------------------- */
/* Daily sending capacity                                                     */
/* -------------------------------------------------------------------------- */

function buildCapacity(): DailyCapacityData {
  const hourly = [
    { hour: '09:00', sent: 0 },
    { hour: '10:00', sent: 0 },
    { hour: '11:00', sent: 0 },
    { hour: '12:00', sent: 0 },
    { hour: '13:00', sent: 0 },
    { hour: '14:00', sent: 0 },
    { hour: '15:00', sent: 0 },
    { hour: '16:00', sent: 0 },
  ];

  return {
    sent: 0,
    limit: DAILY_EMAIL_LIMIT,
    remaining: DAILY_EMAIL_LIMIT,
    queued: 148,
    failed: 0,
    windowLabel: '09:00 – 17:00 (workspace timezone)',
    hourly,
  };
}

/* -------------------------------------------------------------------------- */
/* Today's outreach                                                           */
/* -------------------------------------------------------------------------- */

const outreachFeed: OutreachEvent[] = [
  {
    id: 'evt-1',
    type: 'queued',
    companyName: 'Northwind Logistics',
    contactName: 'Marcus Whitfield',
    subject: 'Cutting fleet idle time across 12 depots',
    campaignName: 'Q3 Ops Leaders — Midwest',
    occurredAt: isoOffset(6 * 60 * 1000),
  },
  {
    id: 'evt-2',
    type: 'queued',
    companyName: 'Brightline Dental Group',
    contactName: 'Dr. Elena Ruiz',
    subject: 'A quick idea for multi-site patient recall',
    campaignName: 'Healthcare Multi-Site',
    occurredAt: isoOffset(24 * 60 * 1000),
  },
  {
    id: 'evt-3',
    type: 'reply',
    companyName: 'Vertex Precision Manufacturing',
    contactName: 'Dale Kowalski',
    subject: 'Re: Reducing scrap rate on CNC line 4',
    campaignName: 'Manufacturing Ops — Phase 2',
    occurredAt: isoOffset(2 * HOUR),
  },
  {
    id: 'evt-4',
    type: 'meeting',
    companyName: 'Halcyon Property Partners',
    contactName: 'Priya Raghavan',
    subject: 'Re: Portfolio reporting consolidation',
    campaignName: 'Real Estate CFOs',
    occurredAt: isoOffset(4 * HOUR),
  },
  {
    id: 'evt-5',
    type: 'sent',
    companyName: 'Copperfield Supply Co.',
    contactName: 'Andre Boateng',
    subject: 'Replacing spreadsheet-based purchasing',
    campaignName: 'Distribution — Southeast',
    occurredAt: isoOffset(6 * HOUR),
  },
  {
    id: 'evt-6',
    type: 'bounce',
    companyName: 'Lakeshore Freight Systems',
    contactName: 'Greg Alderman',
    subject: 'Freight margin visibility in one dashboard',
    campaignName: 'Q3 Ops Leaders — Midwest',
    occurredAt: isoOffset(7 * HOUR),
  },
  {
    id: 'evt-7',
    type: 'sent',
    companyName: 'Summit Ridge Hospitality',
    contactName: 'Nadia Fischer',
    subject: 'Occupancy forecasting without the guesswork',
    campaignName: 'Hospitality Operators',
    occurredAt: isoOffset(9 * HOUR),
  },
];

/* -------------------------------------------------------------------------- */
/* Recent leads                                                               */
/* -------------------------------------------------------------------------- */

const recentLeads: LeadRow[] = [
  {
    id: 'lead-1042',
    companyName: 'Northwind Logistics',
    contactName: 'Marcus Whitfield',
    email: 'm.whitfield@northwindlogistics.com',
    jobTitle: 'VP Operations',
    industry: 'Transportation & Logistics',
    city: 'Columbus',
    state: 'OH',
    website: 'northwindlogistics.com',
    status: 'qualified',
    emailStatus: 'valid',
    score: 92,
    source: 'Dataset import',
    createdAt: isoOffset(2 * HOUR),
  },
  {
    id: 'lead-1041',
    companyName: 'Brightline Dental Group',
    contactName: 'Dr. Elena Ruiz',
    email: 'elena.ruiz@brightlinedental.com',
    jobTitle: 'Managing Partner',
    industry: 'Healthcare',
    city: 'Tampa',
    state: 'FL',
    website: 'brightlinedental.com',
    status: 'contacted',
    emailStatus: 'valid',
    score: 84,
    source: 'Dataset import',
    createdAt: isoOffset(5 * HOUR),
  },
  {
    id: 'lead-1040',
    companyName: 'Vertex Precision Manufacturing',
    contactName: 'Dale Kowalski',
    email: 'dkowalski@vertexprecision.com',
    jobTitle: 'Plant Director',
    industry: 'Manufacturing',
    city: 'Grand Rapids',
    state: 'MI',
    website: 'vertexprecision.com',
    status: 'replied',
    emailStatus: 'valid',
    score: 88,
    source: 'Referral',
    createdAt: isoOffset(9 * HOUR),
  },
  {
    id: 'lead-1039',
    companyName: 'Halcyon Property Partners',
    contactName: 'Priya Raghavan',
    email: 'p.raghavan@halcyonpp.com',
    jobTitle: 'Chief Financial Officer',
    industry: 'Real Estate',
    city: 'Denver',
    state: 'CO',
    website: 'halcyonpp.com',
    status: 'meeting',
    emailStatus: 'valid',
    score: 96,
    source: 'Website form',
    createdAt: isoOffset(12 * HOUR),
  },
  {
    id: 'lead-1038',
    companyName: 'Copperfield Supply Co.',
    contactName: 'Andre Boateng',
    email: 'aboateng@copperfieldsupply.com',
    jobTitle: 'Purchasing Manager',
    industry: 'Wholesale Distribution',
    city: 'Charlotte',
    state: 'NC',
    website: 'copperfieldsupply.com',
    status: 'validated',
    emailStatus: 'risky',
    score: 71,
    source: 'Dataset import',
    createdAt: isoOffset(DAY),
  },
  {
    id: 'lead-1037',
    companyName: 'Lakeshore Freight Systems',
    contactName: 'Greg Alderman',
    email: 'greg@lakeshorefreight.com',
    jobTitle: 'Head of Fleet',
    industry: 'Transportation & Logistics',
    city: 'Milwaukee',
    state: 'WI',
    website: 'lakeshorefreight.com',
    status: 'new',
    emailStatus: 'invalid',
    score: 43,
    source: 'Trade show list',
    createdAt: isoOffset(DAY + 3 * HOUR),
  },
  {
    id: 'lead-1036',
    companyName: 'Summit Ridge Hospitality',
    contactName: 'Nadia Fischer',
    email: 'n.fischer@summitridgehospitality.com',
    jobTitle: 'Regional Director',
    industry: 'Hospitality',
    city: 'Salt Lake City',
    state: 'UT',
    website: 'summitridgehospitality.com',
    status: 'won',
    emailStatus: 'valid',
    score: 90,
    source: 'Referral',
    createdAt: isoOffset(2 * DAY),
  },
];

/* -------------------------------------------------------------------------- */
/* Lead sources                                                               */
/* -------------------------------------------------------------------------- */

const leadSources: LeadSourceBreakdown[] = [
  { id: 'dataset', label: 'Dataset import', count: 16420, share: 57.6, color: sourceSeriesColors[0] },
  { id: 'website', label: 'Website form', count: 4820, share: 16.9, color: sourceSeriesColors[1] },
  { id: 'referral', label: 'Referral', count: 3210, share: 11.3, color: sourceSeriesColors[2] },
  { id: 'outbound', label: 'Outbound prospecting', count: 2410, share: 8.5, color: sourceSeriesColors[3] },
  { id: 'events', label: 'Trade show list', count: 1140, share: 4.0, color: sourceSeriesColors[4] },
  { id: 'partner', label: 'Partner network', count: 490, share: 1.7, color: sourceSeriesColors[5] },
];

/* -------------------------------------------------------------------------- */
/* Campaign overview                                                          */
/* -------------------------------------------------------------------------- */

const campaigns: CampaignSummary[] = [
  {
    id: 'cmp-1',
    name: 'Q3 Ops Leaders — Midwest',
    status: 'active',
    audience: 1840,
    sent: 1216,
    replies: 148,
    meetings: 31,
    progress: 66,
    replyRate: 12.2,
    endsAt: isoInFuture(6 * DAY),
  },
  {
    id: 'cmp-2',
    name: 'Manufacturing Ops — Phase 2',
    status: 'active',
    audience: 960,
    sent: 604,
    replies: 71,
    meetings: 18,
    progress: 63,
    replyRate: 11.8,
    endsAt: isoInFuture(11 * DAY),
  },
  {
    id: 'cmp-3',
    name: 'Healthcare Multi-Site',
    status: 'paused',
    audience: 720,
    sent: 388,
    replies: 42,
    meetings: 12,
    progress: 54,
    replyRate: 10.8,
    endsAt: isoInFuture(18 * DAY),
  },
  {
    id: 'cmp-4',
    name: 'Real Estate CFOs',
    status: 'scheduled',
    audience: 510,
    sent: 0,
    replies: 0,
    meetings: 0,
    progress: 0,
    replyRate: 0,
    endsAt: isoInFuture(24 * DAY),
  },
  {
    id: 'cmp-5',
    name: 'Distribution — Southeast',
    status: 'completed',
    audience: 1420,
    sent: 1420,
    replies: 196,
    meetings: 44,
    progress: 100,
    replyRate: 13.8,
    endsAt: isoOffset(5 * DAY),
  },
];

/* -------------------------------------------------------------------------- */
/* Pipeline                                                                   */
/* -------------------------------------------------------------------------- */

const pipeline: PipelineStage[] = [
  { id: 'contacted', label: 'Contacted', count: 4210, value: 1263000, conversion: 100, tone: 'brand' },
  { id: 'engaged', label: 'Engaged', count: 1128, value: 452000, conversion: 26.8, tone: 'sky' },
  { id: 'meeting', label: 'Meeting booked', count: 312, value: 186000, conversion: 7.4, tone: 'violet' },
  { id: 'opportunity', label: 'Opportunity', count: 46, value: 486000, conversion: 1.1, tone: 'emerald' },
  { id: 'won', label: 'Closed won', count: 12, value: 168000, conversion: 0.3, tone: 'amber' },
];

/* -------------------------------------------------------------------------- */
/* Public builder                                                             */
/* -------------------------------------------------------------------------- */

/**
 * Build the dashboard payload.
 *
 * Written as a function (not a frozen constant) so relative timestamps and the
 * "sent today" counter stay realistic while the UI is being developed.
 */
export function buildMockDashboardOverview(): DashboardOverview {
  const capacity = buildCapacity();

  return {
    generatedAt: new Date().toISOString(),
    metrics: buildMetrics(capacity),
    capacity,
    todaysOutreach: outreachFeed,
    recentLeads,
    leadSources,
    campaigns,
    pipeline,
  };
}

/** Compact pipeline tile value helper (kept next to the data it formats). */
export function pipelineValueLabel(value: number): string {
  return value >= 1000 ? `$${formatCompactNumber(value)}` : formatCurrency(value);
}

export const mockAccent = chartPalette.brand;
