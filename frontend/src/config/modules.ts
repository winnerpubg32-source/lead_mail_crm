/**
 * Module registry for the pages that ship after Phase 1.
 *
 * Each entry is the single description of what that module will do, which
 * columns it will own and where its API lives. The placeholder pages render
 * directly from this file, so the roadmap stays consistent with the sidebar.
 */

export interface ModuleConfig {
  title: string;
  description: string;
  capabilities: string[];
  columns: string[];
  apiPath: string;
  /** Django app that will own the module. */
  djangoApp: string;
}

/**
 * Registry for the modules that still render the shared placeholder page.
 * Leads, Companies and Contacts were implemented in Phase 2 and now have real
 * pages (`src/pages/{LeadsPage,CompaniesPage,ContactsPage}.tsx`).
 */
export const dataColumns = {
  imports: {
    title: 'Imports',
    description:
      'Ingestion runs for large CSV and XLSX business datasets, with column mapping and row-level error reporting.',
    capabilities: [
      'Upload with automatic column mapping and preview of the first rows',
      'Background processing in chunks via Celery — files of hundreds of thousands of rows',
      'Row-level validation errors with downloadable error report',
      'Idempotent re-imports and rollback of a failed run',
    ],
    columns: ['File', 'Rows', 'Processed', 'Failed', 'Status', 'Started', 'Duration', 'Uploaded by'],
    apiPath: '/api/v1/imports/',
    djangoApp: 'imports',
  },
  campaigns: {
    title: 'Campaigns',
    description:
      'Outreach sequences with audiences, multi-step schedules and per-campaign sending budgets.',
    capabilities: [
      'Sequence builder with steps, delays and sending windows',
      'Audience selection from the lead database with live counts',
      'Throttling that respects the 90 e-mails/day workspace limit',
      'Per-campaign reporting on replies and meetings',
    ],
    columns: ['Campaign', 'Status', 'Audience', 'Sent', 'Replies', 'Meetings', 'Reply rate', 'Ends'],
    apiPath: '/api/v1/campaigns/',
    djangoApp: 'campaigns',
  },
  email: {
    title: 'Email',
    description:
      'SMTP mailboxes, the daily 90 e-mail sending budget and delivery diagnostics for every message.',
    capabilities: [
      'SMTP mailbox configuration with encrypted credentials',
      'Hard daily cap of 90 marketing e-mails per workspace',
      'Delivery log with bounce and complaint classification',
      'Warm-up and per-mailbox throttling',
    ],
    columns: ['Message', 'Recipient', 'Mailbox', 'Campaign', 'Status', 'Sent at', 'Opens', 'Error'],
    apiPath: '/api/v1/email/',
    djangoApp: 'email_engine',
  },
  'follow-ups': {
    title: 'Follow-ups',
    description:
      'Automated follow-up steps and manual reminders so no qualified lead is left without a next touch.',
    capabilities: [
      'Automatic follow-up scheduling from campaign step definitions',
      'Reply detection that stops the sequence immediately',
      'Manual reminder queue for account owners',
      'Business-day aware scheduling in the workspace timezone',
    ],
    columns: ['Lead', 'Step', 'Due', 'Channel', 'Status', 'Owner', 'Last touch', 'Next action'],
    apiPath: '/api/v1/campaigns/follow-ups/',
    djangoApp: 'campaigns',
  },
  crm: {
    title: 'CRM',
    description:
      'Deals, notes, tasks and the unified activity timeline that turns replies into revenue.',
    capabilities: [
      'Deal records with stages, amounts and expected close dates',
      'Notes and tasks attached to leads, contacts and companies',
      'Unified activity timeline merging outreach and manual touches',
      'Pipeline forecasting inputs for the analytics module',
    ],
    columns: ['Deal', 'Company', 'Stage', 'Amount', 'Owner', 'Next step', 'Close date', 'Updated'],
    apiPath: '/api/v1/crm/',
    djangoApp: 'crm',
  },
  analytics: {
    title: 'Analytics',
    description:
      'Reporting across outreach volume, reply rates, meetings and pipeline value — the numbers behind the dashboard cards.',
    capabilities: [
      'KPI aggregation by day, week, month, campaign and source',
      'Reply and meeting conversion funnels',
      'Industry and geography performance breakdowns',
      'Exportable reports for weekly reviews',
    ],
    columns: ['Metric', 'Period', 'Value', 'Change', 'Campaign', 'Source', 'Segment', 'Updated'],
    apiPath: '/api/v1/analytics/',
    djangoApp: 'analytics',
  },
  templates: {
    title: 'Templates',
    description:
      'Reusable e-mail templates with variable placeholders, variants and approval state.',
    capabilities: [
      'Template editor with merge fields (company, contact, industry, city, state)',
      'A/B variants with reply-rate comparison',
      'Brand voice and compliance footers',
      'Shared workspace library with usage tracking',
    ],
    columns: ['Template', 'Category', 'Variants', 'Used in', 'Reply rate', 'Owner', 'Updated', 'Status'],
    apiPath: '/api/v1/campaigns/templates/',
    djangoApp: 'campaigns',
  },
  ai: {
    title: 'AI',
    description:
      'AI-assisted lead qualification and personalised B2B outreach copy, with provider and cost tracking.',
    capabilities: [
      'Provider abstraction (OpenAI, Anthropic, self-hosted) with per-workspace keys',
      'Personalisation prompts grounded in company and contact data',
      'Qualification scoring with explainable signals',
      'Token and cost accounting per generation',
    ],
    columns: ['Generation', 'Provider', 'Model', 'Purpose', 'Tokens', 'Cost', 'Lead', 'Created'],
    apiPath: '/api/v1/ai/',
    djangoApp: 'ai_engine',
  },
  suppression: {
    title: 'Suppression',
    description:
      'The global do-not-contact list — unsubscribes, hard bounces and manual blocks, checked before every send.',
    capabilities: [
      'Suppression entries for e-mail addresses and whole domains',
      'One-click unsubscribe handling with audit trail',
      'Bulk suppression list import and export',
      'Pre-send check enforced by the e-mail engine',
    ],
    columns: ['E-mail', 'Domain', 'Reason', 'Source', 'Added by', 'Added at', 'Expires', 'Notes'],
    apiPath: '/api/v1/suppression/',
    djangoApp: 'suppression',
  },
} satisfies Record<string, ModuleConfig>;

export type ModuleKey = keyof typeof dataColumns;
