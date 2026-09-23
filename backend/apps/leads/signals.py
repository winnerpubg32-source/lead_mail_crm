"""
Post-save signal to compute a lead score and log a CREATED activity the first
time a lead enters the database. This is wired up via ``apps.py`` so we don't
have to scatter signal imports into views/tasks.
"""

from __future__ import annotations

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.leads.activity_models import ActivityType
from apps.leads.models import Lead
from apps.leads.scoring import compute_lead_score
from apps.leads.services import log_creation


@receiver(post_save, sender=Lead)
def score_and_log_new_lead(sender, instance: Lead, created: bool, **kwargs) -> None:
    if created:
        # Only auto-compute an initial score when the caller did not specify one
        # (e.g. legacy imports or tests that seed an explicit score).
        if not instance.lead_score:
            score, _ = compute_lead_score(instance)
            if score != 0:
                type(instance).objects.filter(pk=instance.pk).update(lead_score=score)
                instance.lead_score = score
        log_creation(instance, actor="system")
