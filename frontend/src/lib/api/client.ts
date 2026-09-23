import { env } from '@/lib/env';
import type { ApiErrorPayload, ApiFieldErrors } from '@/types/api';

/** Error thrown by the API layer, carrying the backend error envelope. */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: ApiFieldErrors;

  constructor(message: string, status: number, code = 'error', details: ApiFieldErrors = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
  }

  static fromResponse(status: number, payload: unknown): ApiError {
    const envelope = payload as ApiErrorPayload | undefined;
    const error = envelope?.error;
    if (error) {
      return new ApiError(error.message ?? 'Request failed', status, error.code, error.details);
    }
    return new ApiError('Request failed', status);
  }
}

type RequestOptions = Omit<RequestInit, 'body'> & {
  body?: unknown;
  /** Query string parameters; undefined/null values are dropped. */
  query?: Record<string, string | number | boolean | undefined | null>;
  /** Absolute URL override (used for the API root discovery endpoints). */
  absoluteUrl?: string;
};

/** Absolute or relative base for every request (see `lib/env.ts`). */
export function resolveApiBase(): string {
  const override = env.apiUrl.trim();
  return override.length > 0 ? override : env.apiBaseUrl;
}

function buildUrl(path: string, query?: RequestOptions['query']): string {
  const base = resolveApiBase();
  const url = new URL(`${base.replace(/\/$/, '')}/${path.replace(/^\//, '')}`, window.location.origin);
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined && value !== null && value !== '') {
        url.searchParams.set(key, String(value));
      }
    }
  }
  return url.toString();
}

/**
 * Thin fetch wrapper: JSON in, JSON out, backend errors normalised to ApiError.
 *
 * `FormData` bodies bypass JSON serialisation entirely — the browser must set
 * the multipart boundary itself, so the Content-Type header is left off for
 * uploads (see `api.upload`). Authentication tokens are attached from
 * localStorage once the auth phase lands — this is the single place to change.
 */
export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { body, query, absoluteUrl, headers, ...rest } = options;
  const token = typeof localStorage !== 'undefined' ? localStorage.getItem('outreachos.token') : null;
  const isFormData = typeof FormData !== 'undefined' && body instanceof FormData;

  const response = await fetch(absoluteUrl ?? buildUrl(path, query), {
    ...rest,
    headers: {
      Accept: 'application/json',
      ...(body && !isFormData ? { 'Content-Type': 'application/json' } : {}),
      ...(token ? { Authorization: `Token ${token}` } : {}),
      ...headers,
    },
    ...(body ? { body: isFormData ? body : JSON.stringify(body) } : {}),
  });

  if (response.status === 204) return undefined as T;

  const text = await response.text();
  const payload: unknown = text ? JSON.parse(text) : null;

  if (!response.ok) {
    throw ApiError.fromResponse(response.status, payload);
  }

  return payload as T;
}

export const api = {
  get: <T>(path: string, options?: RequestOptions) =>
    apiRequest<T>(path, { ...options, method: 'GET' }),
  post: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    apiRequest<T>(path, { ...options, method: 'POST', body }),
  /** Multipart POST — used for CSV/XLSX uploads. */
  upload: <T>(path: string, body: FormData, options?: RequestOptions) =>
    apiRequest<T>(path, { ...options, method: 'POST', body }),
  patch: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    apiRequest<T>(path, { ...options, method: 'PATCH', body }),
  delete: <T>(path: string, options?: RequestOptions) =>
    apiRequest<T>(path, { ...options, method: 'DELETE' }),
};

/** Resolve a path against the API base — handy for links and diagnostics. */
export function apiUrl(path = ''): string {
  return `${resolveApiBase().replace(/\/$/, '')}/${path.replace(/^\//, '')}`;
}
