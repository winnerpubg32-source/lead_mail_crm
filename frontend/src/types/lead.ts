/**
 * Lead / Company / Contact contracts.
 *
 * These interfaces mirror the Django REST Framework serializers exactly
 * (`backend/apps/{leads,companies,contacts}/serializers.py`). Field names are
 * kept identical to the API so no mapping layer is needed.
 */

/** Pipeline status — values must match `apps.leads.models.LeadStatus`. */
export type LeadStatus =
  | 'NEW'
  | 'QUALIFIED'
  | 'CONTACTED'
  | 'REPLIED'
  | 'MEETING'
  | 'PROPOSAL'
  | 'WON'
  | 'LOST'
  | 'DO_NOT_CONTACT';

/** Deliverability status — values must match `apps.leads.models.EmailStatus`. */
export type EmailStatus =
  | 'UNKNOWN'
  | 'VALID'
  | 'INVALID'
  | 'BOUNCED'
  | 'UNSUBSCRIBED'
  | 'SUPPRESSED';

export type PhoneType = 'UNKNOWN' | 'MOBILE' | 'LANDLINE' | 'OFFICE' | 'OTHER';

/** `GET /api/v1/leads/` row. */
export interface Lead {
  id: number;
  company: number | null;
  company_name: string;
  contact: number | null;
  contact_name: string;
  job_title: string;
  email: string;
  phone: string;
  industry: string;
  city: string;
  state: string;
  lead_score: number;
  lead_status: LeadStatus;
  lead_status_display: string;
  email_status: EmailStatus;
  email_status_display: string;
  source: string;
  source_file: string;
  source_row_number: number | null;
  is_contactable: boolean;
  created_at: string;
  updated_at: string;
}

/** `GET /api/v1/companies/` row. */
export interface Company {
  id: number;
  name: string;
  normalized_name?: string;
  industry: string;
  sub_industry: string;
  website: string;
  normalized_website: string;
  domain?: string;
  phone: string;
  normalized_phone?: string;
  street_address?: string;
  city: string;
  state: string;
  zip_code?: string;
  country: string;
  employee_count: number | null;
  source: string;
  location: string;
  lead_count: number;
  contact_count: number;
  created_at: string;
  updated_at: string;
}

/** `GET /api/v1/contacts/` row. */
export interface Contact {
  id: number;
  company: number | null;
  company_name: string;
  first_name: string;
  last_name: string;
  full_name: string;
  job_title: string;
  email: string;
  normalized_email: string;
  phone: string;
  normalized_phone?: string;
  phone_type: PhoneType;
  company_industry?: string;
  company_city?: string;
  company_state?: string;
  created_at: string;
  updated_at: string;
}

/** Enum vocabulary returned by `GET /api/v1/leads/statuses/`. */
export interface StatusChoice {
  value: string;
  label: string;
  count: number;
}

export interface LeadStatusVocabulary {
  lead_status: StatusChoice[];
  email_status: StatusChoice[];
  total: number;
  defaults: { lead_status: LeadStatus; email_status: EmailStatus };
}

/** Query parameters understood by every list endpoint. */
export interface ListParams {
  page?: number;
  page_size?: number;
  search?: string;
  ordering?: string;
  [filter: string]: string | number | boolean | undefined;
}
