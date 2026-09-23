# Email engine

**Phase 1 status:** registered, routed, empty.

Planned purpose: SMTP delivery with a hard cap of 90 marketing e-mails per day.

Planned capabilities:
  - Daily send budget with Redis counter (max 90/day)
  - Per-mailbox SMTP configuration stored encrypted
  - Bounce/complaint handling and automatic suppression
