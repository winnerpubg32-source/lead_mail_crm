import { useState } from 'react';

import type { ListParams } from '@/types/lead';

export type SortDirection = 'asc' | 'desc';

export interface ListQueryState {
  page: number;
  pageSize: number;
  search: string;
  ordering: string;
  filters: Record<string, string>;
}

const DEFAULTS: ListQueryState = {
  page: 1,
  pageSize: 25,
  search: '',
  ordering: '',
  filters: {},
};

/**
 * State container for a paginated, searchable, filterable list page.
 *
 * Keeping it in one hook means the leads/companies/contacts pages share the
 * exact same behaviour (reset to page 1 on any change, clear filters, etc.).
 */
export function useListQuery(initial: Partial<ListQueryState> = {}) {
  const [state, setState] = useState<ListQueryState>({ ...DEFAULTS, ...initial });

  /** Change the search term — always returns to the first page. */
  const setSearch = (search: string) => setState((prev) => ({ ...prev, search, page: 1 }));

  const setPage = (page: number) => setState((prev) => ({ ...prev, page: Math.max(1, page) }));

  const setPageSize = (pageSize: number) =>
    setState((prev) => ({ ...prev, pageSize, page: 1 }));

  const setFilter = (key: string, value: string) =>
    setState((prev) => {
      const filters = { ...prev.filters };
      if (value === '') {
        delete filters[key];
      } else {
        filters[key] = value;
      }
      return { ...prev, filters, page: 1 };
    });

  const setFilters = (filters: Record<string, string>) =>
    setState((prev) => ({ ...prev, filters, page: 1 }));

  /** Toggle ordering for a column: asc → desc → (default). */
  const toggleOrdering = (field: string) =>
    setState((prev) => {
      if (prev.ordering === field) return { ...prev, ordering: `-${field}`, page: 1 };
      if (prev.ordering === `-${field}`) return { ...prev, ordering: '', page: 1 };
      return { ...prev, ordering: field, page: 1 };
    });

  const reset = () => setState({ ...DEFAULTS, ...initial });

  /** Normalise into DRF query parameters (empty values are dropped by the client). */
  const params: ListParams = {
    page: state.page,
    page_size: state.pageSize,
    search: state.search || undefined,
    ordering: state.ordering || undefined,
    ...state.filters,
  };

  const activeFilterCount = Object.keys(state.filters).length;
  const hasActiveQuery = Boolean(state.search) || activeFilterCount > 0;

  return {
    ...state,
    params,
    activeFilterCount,
    hasActiveQuery,
    setSearch,
    setPage,
    setPageSize,
    setFilter,
    setFilters,
    toggleOrdering,
    reset,
  };
}

/** Sort indicator for a table header cell. */
export function sortDirectionFor(ordering: string, field: string): SortDirection | null {
  if (ordering === field) return 'asc';
  if (ordering === `-${field}`) return 'desc';
  return null;
}
