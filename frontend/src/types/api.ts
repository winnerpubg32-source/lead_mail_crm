/** Backend error envelope — mirrors core/exceptions.py on the Django side. */
export interface ApiFieldErrors {
  [field: string]: string | string[] | undefined;
}

export interface ApiErrorBody {
  code: string;
  message: string;
  details?: ApiFieldErrors;
}

export interface ApiErrorPayload {
  error?: ApiErrorBody;
}

/** DRF page-number pagination envelope. */
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface HealthResponse {
  status: string;
  service?: string;
  version?: string;
  environment?: string;
  time?: string;
}
