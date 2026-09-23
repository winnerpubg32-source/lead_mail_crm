import { Ban, CheckCheck, CircleSlash, Mail, MailCheck, MailWarning, Send, Sparkles, Target } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

import type { BadgeTone } from '@/components/ui/Badge';
import type { OutreachEventType } from '@/types/dashboard';
import type { EmailStatus, LeadStatus, PhoneType, ScoreClassification } from '@/types/lead';
import type { CampaignStatus as CampaignStatusCode } from '@/types/campaign';

/**
 * Presentation metadata for every domain enum.
 *
 * Kept out of the components so badges look identical in tables, cards, filters
 * and the (future) lead detail drawer — and so a backend value rename touches
 * exactly one file.
 */

export interface StatusPresentation {
  label: string;
  tone: BadgeTone;
}

/** Pipeline statuses — keys match `apps.leads.models.LeadStatus` exactly. */
export const leadStatusConfig: Record<LeadStatus, StatusPresentation> = {
  NEW: { label: 'New', tone: 'neutral' },
  QUALIFIED: { label: 'Qualified', tone: 'violet' },
  CONTACTED: { label: 'Contacted', tone: 'brand' },
  REPLIED: { label: 'Replied', tone: 'info' },
  MEETING: { label: 'Meeting', tone: 'success' },
  PROPOSAL: { label: 'Proposal', tone: 'warning' },
  WON: { label: 'Won', tone: 'success' },
  LOST: { label: 'Lost', tone: 'danger' },
  DO_NOT_CONTACT: { label: 'Do not contact', tone: 'neutral' },
  MERGED: { label: 'Merged', tone: 'neutral' },
};

/** Deliverability statuses — keys match `apps.leads.models.EmailStatus`. */
export const emailStatusConfig: Record<EmailStatus, StatusPresentation> = {
  UNKNOWN: { label: 'Unknown', tone: 'neutral' },
  VALID: { label: 'Valid', tone: 'success' },
  INVALID: { label: 'Invalid', tone: 'danger' },
  BOUNCED: { label: 'Bounced', tone: 'danger' },
  UNSUBSCRIBED: { label: 'Unsubscribed', tone: 'warning' },
  SUPPRESSED: { label: 'Suppressed', tone: 'neutral' },
};

/** Campaign lifecycle badges (Phase 6). */
export const campaignStatusConfig: Record<CampaignStatusCode | string, StatusPresentation> = {
  DRAFT: { label: 'Draft', tone: 'neutral' },
  READY: { label: 'Ready', tone: 'info' },
  RUNNING: { label: 'Running', tone: 'success' },
  PAUSED: { label: 'Paused', tone: 'warning' },
  COMPLETED: { label: 'Completed', tone: 'brand' },
  CANCELLED: { label: 'Cancelled', tone: 'neutral' },
  // Legacy lowercase keys used by the dashboard mock data.
  draft: { label: 'Draft', tone: 'neutral' },
  scheduled: { label: 'Scheduled', tone: 'info' },
  active: { label: 'Active', tone: 'success' },
  paused: { label: 'Paused', tone: 'warning' },
  completed: { label: 'Completed', tone: 'brand' },
};

export const phoneTypeLabels: Record<PhoneType, string> = {
  UNKNOWN: 'Unknown',
  MOBILE: 'Mobile',
  LANDLINE: 'Landline',
  OFFICE: 'Office',
  OTHER: 'Other',
};

/** Statuses shown as the primary pipeline filter on the leads page. */
export const primaryLeadStatusOrder: LeadStatus[] = [
  'NEW',
  'QUALIFIED',
  'CONTACTED',
  'REPLIED',
  'MEETING',
  'PROPOSAL',
  'WON',
  'LOST',
  'DO_NOT_CONTACT',
];

export interface OutreachEventPresentation extends StatusPresentation {
  icon: LucideIcon;
}

export const outreachEventConfig: Record<OutreachEventType, OutreachEventPresentation> = {
  sent: { label: 'Sent', tone: 'brand', icon: Send },
  queued: { label: 'Queued', tone: 'neutral', icon: Mail },
  reply: { label: 'Reply', tone: 'success', icon: MailCheck },
  bounce: { label: 'Bounce', tone: 'danger', icon: MailWarning },
  meeting: { label: 'Meeting', tone: 'violet', icon: Target },
  unsubscribe: { label: 'Unsubscribed', tone: 'warning', icon: Ban },
};

/** Score → badge tone for the qualification column. Phase 5: HOT/WARM/COLD/UNQUALIFIED. */
export function scoreTone(score: number, blocked = false): BadgeTone {
  if (blocked || score < 20) return 'neutral';
  if (score >= 70) return 'success';
  if (score >= 50) return 'warning';
  return 'brand';
}

/** Phase 5: explicit classification classification from the API, with score fallback. */
export function scoreClassification(code: ScoreClassification | undefined, score: number): ScoreClassification {
  if (code) return code;
  if (score >= 70) return 'HOT';
  if (score >= 50) return 'WARM';
  if (score >= 20) return 'COLD';
  return 'UNQUALIFIED';
}

export const scoreClassificationConfig: Record<ScoreClassification, { label: string; tone: BadgeTone }> = {
  HOT: { label: 'Hot', tone: 'success' },
  WARM: { label: 'Warm', tone: 'warning' },
  COLD: { label: 'Cold', tone: 'brand' },
  UNQUALIFIED: { label: 'Unqualified', tone: 'neutral' },
};

/** Score → square chip classes (denser than a badge, keeps tables scannable). Phase 5: HOT/WARM/COLD/UNQUALIFIED. */
export function scoreChipClass(score: number, blocked = false): string {
  if (blocked || score < 20) {
    return 'bg-surface-3 text-muted ring-border-subtle';
  }
  if (score >= 70) {
    return 'bg-emerald-50 text-emerald-700 ring-emerald-200 dark:bg-emerald-500/10 dark:text-emerald-300 dark:ring-emerald-500/20';
  }
  if (score >= 50) {
    return 'bg-amber-50 text-amber-700 ring-amber-200 dark:bg-amber-500/10 dark:text-amber-300 dark:ring-amber-500/20';
  }
  return 'bg-sky-50 text-sky-700 ring-sky-200 dark:bg-sky-500/10 dark:text-sky-300 dark:ring-sky-500/20';
}

export const ACTIVITY_ICONS: Record<string, string> = {
  CREATED: '✨',
  STATUS_CHANGE: '🔁',
  SCORE_CHANGE: '📈',
  NOTE_ADDED: '📝',
  EMAIL_SENT: '📤',
  EMAIL_OPENED: '👁️',
  REPLY: '↩️',
  MEETING: '📅',
  MERGED: '🔀',
  SUPPRESSED: '🚫',
  BULK_EDIT: '⚙️',
  CAMPAIGN_ADDED: '📣',
  EXPORTED: '⬇️',
  MANUAL_EDIT: '✏️',
  VALIDATION: '🧪',
};

/** Utility used by "Phase 2" module pages. */
export const comingSoonIcon = Sparkles;

/** Fallback icon set re-exported for convenience in placeholder pages. */
export { CircleSlash, CheckCheck };
