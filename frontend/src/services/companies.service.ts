/** Companies data access — `GET /api/v1/companies/`. */

import { api } from '@/lib/api/client';
import type { PaginatedResponse } from '@/types/api';
import type { Company, ListParams } from '@/types/lead';

export const companyKeys = {
  all: ['companies'] as const,
  list: (params: ListParams) => [...companyKeys.all, 'list', params] as const,
  detail: (id: number) => [...companyKeys.all, 'detail', id] as const,
};

export function fetchCompanies(params: ListParams = {}): Promise<PaginatedResponse<Company>> {
  return api.get<PaginatedResponse<Company>>('v1/companies/', { query: params });
}

export function fetchCompany(id: number): Promise<Company> {
  return api.get<Company>(`v1/companies/${id}/`);
}
