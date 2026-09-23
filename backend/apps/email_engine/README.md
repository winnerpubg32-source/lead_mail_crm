# Email engine

Phase 7 owns SMTP delivery on top of the Phase 6 campaign queue.

## Delivery flow

A campaign moving to `RUNNING` renders its selected `EmailTemplate` against each
prepared `CampaignLead` and creates one `EmailMessage` in `QUEUED` state. Celery
beat dispatches due messages to workers. Workers atomically claim the message,
reserve a slot in `DailyEmailUsage`, and send through Django's configured email
backend.

SMTP configuration is read only by Django/Celery:

- `EMAIL_BACKEND`
- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `EMAIL_USE_TLS`
- `DEFAULT_FROM_EMAIL`

The global default is 90 marketing reservations per workspace-local day. The
conditional database update on `DailyEmailUsage` is safe across concurrent
workers. Same-day retries reuse the message's reservation and a successful
message is idempotent when a task is redelivered.

## API

- `GET /api/v1/email/usage/`
- `GET /api/v1/email/messages/`
- `GET /api/v1/email/messages/{id}/`
- `GET /api/v1/email/messages/statuses/`
- Phase 6 template CRUD and preview routes under `/api/v1/email/templates/`
