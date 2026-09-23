/**
 * Data-quality types (Phase 4).
 * Mirrors backend serializers in apps/data_quality/serializers.py.
 */

import type { Lead } from '@/types/lead';
import type { PaginatedResponse } from '@/types/api';

export interface DataQualityStats {
  total_leads: number;
  valid_emails: number;
  invalid_emails: number;
  missing_emails: number;
  missing_phones: number;
  missing_websites: number;
  duplicate_groups: number;
  missing_contact_names: number;
}

export type DuplicateReasonCode =
  | 'EMAIL'
  | 'COMPANY_WEBSITE'
  | 'COMPANY_PHONE'
  | 'COMPANY_ADDRESS'
  | 'COMPANY_CITY_STATE'
  | 'CONTACT_NAME_COMPANY';

export type DuplicateGroupStatus = 'OPEN' | 'MERGED' | 'KEPT_BOTH' | 'IGNORED';

export interface DuplicateGroupMember {
  id: number;
  role: 'A' | 'B';
  lead: Lead;
}

export interface DuplicateGroup {
  id: number;
  reason_code: DuplicateReasonCode;
  reason_label: string;
  confidence: number;
  status: DuplicateGroupStatus;
  status_label: string;
  cluster_key?: string;
  members: DuplicateGroupMember[];
  record_a: Lead | null;
  record_b: Lead | null;
  created_at: string;
  updated_at: string;
}

export interface MergeAuditEntry {
  id: number;
  surviving_lead: number;
  merged_lead: number;
  reason_code: DuplicateReasonCode | '';
  confidence: number;
  fields_from_merged: Record<string, unknown>;
  merged_sources: Array<{ source: string; source_file: string; source_row_number: number | null; lead: number }>;
  performed_by: string;
  created_at: string;
}

export interface MissingEmailLead extends Lead {
  website?: string;
  country?: string;
}

export interface DetectDuplicatesResult {
  new_groups: number;
  EMAIL: number;
  COMPANY_WEBSITE: number;
  COMPANY_PHONE: number;
  COMPANY_ADDRESS: number;
  COMPANY_CITY_STATE: number;
  CONTACT_NAME_COMPANY: number;
}

export type DuplicateGroupList = PaginatedResponse<DuplicateGroup>;
export type MissingEmailList = PaginatedResponse<MissingEmailLead>;
export type MergeAuditList = PaginatedResponse<MergeAuditEntry>;
