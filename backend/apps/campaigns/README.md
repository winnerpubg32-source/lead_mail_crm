# Campaigns

Phase 6 provides audience targeting, reusable templates, campaign lifecycle
states, and the `CampaignLead` audience snapshot. Phase 7 connects the launch
boundary to SMTP delivery:

1. `prepare_campaign()` validates and snapshots eligible leads as `PENDING`.
2. Transitioning to `RUNNING` renders the selected template and creates one
   `EmailMessage` per pending membership.
3. Memberships become `QUEUED`; Celery workers deliver them over the configured
   sending window.
4. Delivery updates `CampaignLead`, campaign counters, and lead activities.

Campaigns support optional `sending_start_time` and `sending_end_time` fields.
Unset values use the workspace defaults `OUTREACH_SENDING_START_TIME` and
`OUTREACH_SENDING_END_TIME`. The global `OUTREACH_DAILY_EMAIL_LIMIT` remains a
hard, concurrency-safe quota enforced by the email engine.
