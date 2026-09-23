/**
 * Campaigns + templates data access (Phase 6).
 */

import { api } from '@/lib/api/client';
import type {
  Campaign,
  CampaignMember,
  CampaignStatusChoice,
  CampaignWizardDraft,
  EmailTemplate,
  TemplatePreview,
} from '@/types/campaign';
import type { ListParams } from '@/types/lead';
import type { PaginatedResponse } from '@/types/api';
import type { Lead } from '@/types/lead';

export const campaignKeys = {
  all: ['campaigns'] as const,
  list: (params: ListParams) => [...campaignKeys.all, 'list', params] as const,
  detail: (id: number) => [...campaignKeys.all, 'detail', id] as const,
  statuses: () => [...campaignKeys.all, 'statuses'] as const,
  members: (id: number) => [...campaignKeys.all, 'members', id] as const,
  templates: () => ['templates'] as const,
  templateDetail: (id: number) => ['templates', id] as const,
};

// ----------------- Campaigns -----------------
export function fetchCampaigns(params: ListParams = {}): Promise<PaginatedResponse<Campaign>> {
  return api.get<PaginatedResponse<Campaign>>('v1/campaigns/', { query: params });
}

export function fetchCampaign(id: number): Promise<Campaign> {
  return api.get<Campaign>(`v1/campaigns/${id}/`);
}

export function createCampaign(payload: Partial<CampaignWizardDraft>): Promise<Campaign> {
  return api.post<Campaign>('v1/campaigns/', payload);
}

export function updateCampaign(id: number, patch: Partial<CampaignWizardDraft>): Promise<Campaign> {
  return api.patch<Campaign>(`v1/campaigns/${id}/`, patch);
}

export function deleteCampaign(id: number): Promise<void> {
  return api.delete<void>(`v1/campaigns/${id}/`);
}

export function setCampaignStatus(
  id: number,
  status: Campaign['status'],
): Promise<Campaign> {
  return api.post<Campaign>(`v1/campaigns/${id}/status/`, { status });
}

export function prepareCampaign(id: number): Promise<{
  status: Campaign['status'];
  eligible_count: number;
  campaign: Campaign;
  message: string;
}> {
  return api.post(`v1/campaigns/${id}/prepare/`);
}

export function validateCampaign(id: number): Promise<{
  valid: boolean;
  errors: string[];
  eligible_count: number;
}> {
  return api.get(`v1/campaigns/${id}/validate/`);
}

export function fetchCampaignAudiencePreview(
  id: number,
  params: ListParams = {},
): Promise<PaginatedResponse<Lead>> {
  return api.get(`v1/campaigns/${id}/preview-audience/`, { query: params });
}

export function fetchCampaignMembers(
  id: number,
  params: ListParams = {},
): Promise<PaginatedResponse<CampaignMember>> {
  return api.get(`v1/campaigns/${id}/members/`, { query: params });
}

export function fetchCampaignStatuses(): Promise<{
  campaign_status: CampaignStatusChoice[];
  default_daily_limit: number;
  total: number;
}> {
  return api.get('v1/campaigns/statuses/');
}

// ----------------- Templates -----------------
export function fetchTemplates(): Promise<EmailTemplate[]> {
  return api.get<EmailTemplate[]>('v1/email/templates/');
}

export function fetchTemplate(id: number): Promise<EmailTemplate> {
  return api.get<EmailTemplate>(`v1/email/templates/${id}/`);
}

export function createTemplate(payload: Partial<EmailTemplate>): Promise<EmailTemplate> {
  return api.post<EmailTemplate>('v1/email/templates/', payload);
}

export function updateTemplate(id: number, patch: Partial<EmailTemplate>): Promise<EmailTemplate> {
  return api.patch<EmailTemplate>(`v1/email/templates/${id}/`, patch);
}

export function deleteTemplate(id: number): Promise<void> {
  return api.delete<void>(`v1/email/templates/${id}/`);
}

export function previewTemplate(id: number, context?: Record<string, string>): Promise<TemplatePreview> {
  return api.post<TemplatePreview>(`v1/email/templates/${id}/preview/`, { context: context ?? {} });
}

export function previewTemplateInline(
  subject: string,
  body: string,
  context?: Record<string, string>,
): Promise<TemplatePreview> {
  return api.post<TemplatePreview>('v1/email/templates/preview-inline/', {
    subject,
    body,
    context: context ?? {},
  });
}

export function fetchTemplateVariables(): Promise<{
  supported_variables: string[];
  sample_lead: Record<string, string>;
}> {
  return api.get('v1/email/templates/variables/');
}
