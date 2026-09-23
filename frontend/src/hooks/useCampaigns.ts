import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { emailKeys, fetchDailyEmailUsage } from '@/services/email.service';

import {
  campaignKeys,
  createCampaign,
  createTemplate,
  deleteCampaign,
  deleteTemplate,
  fetchCampaign,
  fetchCampaignAudiencePreview,
  fetchCampaignMembers,
  fetchCampaigns,
  fetchCampaignStatuses,
  fetchTemplate,
  fetchTemplates,
  fetchTemplateVariables,
  prepareCampaign,
  previewTemplate,
  previewTemplateInline,
  setCampaignStatus,
  updateCampaign,
  updateTemplate,
  validateCampaign,
} from '@/services/campaigns.service';
import type { CampaignWizardDraft, EmailTemplate } from '@/types/campaign';
import type { ListParams } from '@/types/lead';

export function useCampaigns(params: ListParams) {
  return useQuery({
    queryKey: campaignKeys.list(params),
    queryFn: () => fetchCampaigns(params),
    placeholderData: (previous) => previous,
  });
}

export function useCampaign(id: number) {
  return useQuery({
    queryKey: campaignKeys.detail(id),
    queryFn: () => fetchCampaign(id),
    enabled: Number.isFinite(id) && id > 0,
  });
}

export function useCampaignStatuses() {
  return useQuery({
    queryKey: campaignKeys.statuses(),
    queryFn: fetchCampaignStatuses,
    staleTime: 60_000,
  });
}

export function useCreateCampaign() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: Partial<CampaignWizardDraft>) => createCampaign(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: campaignKeys.all }),
  });
}

export function useUpdateCampaign() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, patch }: { id: number; patch: Partial<CampaignWizardDraft> }) =>
      updateCampaign(id, patch),
    onSuccess: (_data, { id }) => {
      qc.invalidateQueries({ queryKey: campaignKeys.all });
      qc.invalidateQueries({ queryKey: campaignKeys.detail(id) });
    },
  });
}

export function useDeleteCampaign() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: deleteCampaign,
    onSuccess: () => qc.invalidateQueries({ queryKey: campaignKeys.all }),
  });
}

export function useCampaignStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, status }: { id: number; status: ReturnType<typeof String> }) =>
      setCampaignStatus(id, status as never),
    onSuccess: (_data, { id }) => {
      qc.invalidateQueries({ queryKey: campaignKeys.all });
      qc.invalidateQueries({ queryKey: campaignKeys.detail(id) });
    },
  });
}

export function usePrepareCampaign() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => prepareCampaign(id),
    onSuccess: (_data, id) => {
      qc.invalidateQueries({ queryKey: campaignKeys.all });
      qc.invalidateQueries({ queryKey: campaignKeys.detail(id) });
    },
  });
}

export function useValidateCampaign(id: number) {
  return useQuery({
    queryKey: [...campaignKeys.detail(id), 'validate'],
    queryFn: () => validateCampaign(id),
    enabled: Number.isFinite(id) && id > 0,
    refetchInterval: 15_000,
  });
}

export function useCampaignAudience(id: number, params: ListParams = {}) {
  return useQuery({
    queryKey: [...campaignKeys.detail(id), 'audience', params],
    queryFn: () => fetchCampaignAudiencePreview(id, params),
    enabled: Number.isFinite(id) && id > 0,
  });
}

export function useCampaignMembers(id: number, params: ListParams = {}) {
  return useQuery({
    queryKey: campaignKeys.members(id),
    queryFn: () => fetchCampaignMembers(id, params),
    enabled: Number.isFinite(id) && id > 0,
  });
}

// ----------------- Templates -----------------
export function useTemplates() {
  return useQuery({
    queryKey: campaignKeys.templates(),
    queryFn: fetchTemplates,
    staleTime: 30_000,
  });
}

export function useTemplate(id: number) {
  return useQuery({
    queryKey: campaignKeys.templateDetail(id),
    queryFn: () => fetchTemplate(id),
    enabled: Number.isFinite(id) && id > 0,
  });
}

export function useCreateTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: Partial<EmailTemplate>) => createTemplate(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: campaignKeys.templates() });
      qc.invalidateQueries({ queryKey: campaignKeys.all });
    },
  });
}

export function useUpdateTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, patch }: { id: number; patch: Partial<EmailTemplate> }) => updateTemplate(id, patch),
    onSuccess: (_data, { id }) => {
      qc.invalidateQueries({ queryKey: campaignKeys.templates() });
      qc.invalidateQueries({ queryKey: campaignKeys.templateDetail(id) });
    },
  });
}

export function useDeleteTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: deleteTemplate,
    onSuccess: () => qc.invalidateQueries({ queryKey: campaignKeys.templates() }),
  });
}

export function useTemplateVariables() {
  return useQuery({
    queryKey: ['templates', 'variables'],
    queryFn: fetchTemplateVariables,
    staleTime: 600_000,
  });
}

export function usePreviewTemplate(id: number | null, context?: Record<string, string>) {
  return useQuery({
    queryKey: ['templates', 'preview', id, context],
    queryFn: () => previewTemplate(id!, context),
    enabled: !!id,
  });
}

export function usePreviewInline(subject: string, body: string) {
  return useQuery({
    queryKey: ['templates', 'preview-inline', subject, body],
    queryFn: () => previewTemplateInline(subject, body),
    enabled: body.length > 9,
    staleTime: 1000,
    refetchOnWindowFocus: false,
    retry: false,
  });
}

export function useDailyEmailUsage(enabled = true) {
  return useQuery({
    queryKey: emailKeys.usage(),
    queryFn: fetchDailyEmailUsage,
    enabled,
    refetchInterval: 30_000,
    staleTime: 10_000,
  });
}
