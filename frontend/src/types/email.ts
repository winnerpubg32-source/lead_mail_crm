export interface DailyEmailUsage {
  date: string;
  sent_today: number;
  limit: number;
  remaining: number;
  progress_pct: number;
  queued: number;
  failed: number;
  window_label: string;
}
