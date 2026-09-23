"""OutreachOS domain applications.

Each module owns one bounded context so features can be added in later phases
without touching the rest of the code base:

accounts      users, authentication, workspace membership
companies     imported businesses (name, website, industry, city, state)
contacts      people attached to companies (name, title, e-mail, phone)
leads         qualified prospects + status pipeline
imports       CSV/XLSX ingestion runs and row level errors
campaigns     outreach sequences and their audience
email_engine  SMTP delivery, daily limits (max 90/day), bounces
ai_engine     personalisation / qualification prompts and providers
crm           deals, notes, tasks, activity timeline
analytics     aggregated reporting metrics
suppression   global do-not-contact list (unsubscribes, bounces)
"""
