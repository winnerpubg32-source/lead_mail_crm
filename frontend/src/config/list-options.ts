/**
 * Filter option lists for the list pages.
 *
 * Labels mirror Django's `TextChoices` (see `apps/leads/models.py`) — the API
 * returns the value, this module supplies the human label for selects.
 */

import { emailStatusConfig, leadStatusConfig, phoneTypeLabels, primaryLeadStatusOrder } from '@/config/status';

export const leadStatusOptions = primaryLeadStatusOrder.map((value) => ({
  value,
  label: leadStatusConfig[value].label,
}));

export const emailStatusOptions = (
  Object.keys(emailStatusConfig) as Array<keyof typeof emailStatusConfig>
).map((value) => ({ value, label: emailStatusConfig[value].label }));

export const phoneTypeOptions = (
  Object.keys(phoneTypeLabels) as Array<keyof typeof phoneTypeLabels>
).map((value) => ({ value, label: phoneTypeLabels[value] }));

/** Common industry values used by the demo dataset (free-text on the model). */
export const industryOptions = [
  'Construction',
  'Financial Services',
  'Healthcare',
  'Hospitality',
  'Manufacturing',
  'Professional Services',
  'Real Estate',
  'Retail',
  'Transportation & Logistics',
  'Wholesale Distribution',
].map((value) => ({ value, label: value }));

/** The 20 states present in the seeded dataset plus common business states. */
export const stateOptions = [
  'AZ',
  'CO',
  'FL',
  'IA',
  'ID',
  'IN',
  'KY',
  'MI',
  'MO',
  'NC',
  'NE',
  'NM',
  'NY',
  'OH',
  'OR',
  'TN',
  'UT',
  'VA',
  'WI',
].map((value) => ({ value, label: value }));

export const sourceOptions = [
  { value: 'dataset_import', label: 'Dataset import' },
  { value: 'website_form', label: 'Website form' },
  { value: 'referral', label: 'Referral' },
  { value: 'outbound_prospecting', label: 'Outbound prospecting' },
  { value: 'trade_show_list', label: 'Trade show list' },
  { value: 'partner_network', label: 'Partner network' },
];

/** Human label for a raw source value. */
export function sourceLabel(value: string): string {
  if (!value) return '—';
  return sourceOptions.find((option) => option.value === value)?.label ?? value.replace(/_/g, ' ');
}

/** Priority tiers used as quick score filters on the leads page (Phase 5). */
export const scoreFilterOptions = [
  { value: 'HOT', label: 'Hot (≥ 70)' },
  { value: 'WARM', label: 'Warm (50–69)' },
  { value: 'COLD', label: 'Cold (20–49)' },
  { value: 'UNQUALIFIED', label: 'Unqualified (< 20)' },
];

/** Fallback city list — the backend supplies live distinct values when available. */
export const cityOptions = [{ value: '', label: 'All cities' }];
