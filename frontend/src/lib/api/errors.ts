import { ApiError } from '@/lib/api/client';
import type { ApiFieldErrors } from '@/types/api';

/** First message in a DRF field-error list (`{file: ["Unsupported…"]}`). */
export function firstApiDetail(details: ApiFieldErrors | undefined, keys: string[]): string | undefined {
  if (!details) return undefined;
  for (const key of keys) {
    const value = details[key];
    if (typeof value === 'string') return value;
    if (Array.isArray(value) && value.length > 0) return String(value[0]);
  }
  return undefined;
}

/**
 * Human-readable message for a failed request.
 *
 * Field-level details win over the generic envelope message — "Unsupported file
 * type. Upload a .csv…" is far more useful than "Request could not be processed."
 */
export function apiErrorMessage(error: unknown, keys: string[] = [], fallback = 'Something went wrong.'): string {
  if (error instanceof ApiError) {
    return firstApiDetail(error.details, keys) ?? error.message ?? fallback;
  }
  if (error instanceof Error && error.message) return error.message;
  return fallback;
}
