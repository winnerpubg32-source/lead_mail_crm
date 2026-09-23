import { Ban, CheckCheck, CircleSlash, Mail, MailCheck, MailWarning, Send, Sparkles, Target } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

import type { BadgeTone } from '@/components/ui/Badge';
import type { CampaignStatus, OutreachEventType } from '@/types/dashboard';
import type { EmailStatus, LeadStatus, PhoneType } from '@/types/lead';

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

export const campaignStatusConfig: Record<CampaignStatus, StatusPresentation> = {
  draft: { label: 'Draft', tone: 'neutral' },
  scheduled: { label: 'Scheduled', tone: 'info' },
  active: { label: 'Active', tone: 'success' },
  paused: { label: 'Paused', tone: 'warning' },
  completed: { label: 'Completed', tone: 'brand' },
};

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

/** Score → badge tone for the qualification column. */
export function scoreTone(score: number): BadgeTone {
  if (score >= 85) return 'success';
  if (score >= 70) return 'brand';
  if (score >= 50) return 'warning';
  return 'neutral';
}

/** Score → square chip classes (denser than a badge, keeps tables scannable). */
export function scoreChipClass(score: number): string {
  if (score >= 85) {
    return 'bg-emerald-50 text-emerald-700 ring-emerald-200 dark:bg-emerald-500/10 dark:text-emerald-300 dark:ring-emerald-500/20';
  }
  if (score >= 70) {
    return 'bg-brand-50 text-brand-700 ring-brand-200 dark:bg-brand-500/10 dark:text-brand-200 dark:ring-brand-500/20';
  }
  return 'bg-surface-3 text-muted ring-border-subtle';
}

/** Utility used by "Phase 2" module pages. */
export const comingSoonIcon = Sparkles;

/** Fallback icon set re-exported for convenience in placeholder pages. */
export { CircleSlash, CheckCheck };
