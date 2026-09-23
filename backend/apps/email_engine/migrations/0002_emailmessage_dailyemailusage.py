# Generated manually for Phase 7 SMTP delivery.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("campaigns", "0001_initial"),
        ("email_engine", "0001_initial"),
        ("leads", "0003_leadactivity_leadnote"),
    ]

    operations = [
        migrations.CreateModel(
            name="DailyEmailUsage",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("date", models.DateField(db_index=True, unique=True)),
                ("sent_count", models.PositiveIntegerField(default=0)),
                ("limit", models.PositiveIntegerField(default=90)),
            ],
            options={"ordering": ("-date",)},
        ),
        migrations.CreateModel(
            name="EmailMessage",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("to_email", models.EmailField(max_length=320)),
                ("subject", models.CharField(max_length=255)),
                ("body", models.TextField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("QUEUED", "Queued"),
                            ("PROCESSING", "Processing"),
                            ("SENT", "Sent"),
                            ("FAILED", "Failed"),
                            ("CANCELLED", "Cancelled"),
                            ("BOUNCED", "Bounced"),
                        ],
                        db_index=True,
                        default="QUEUED",
                        max_length=20,
                    ),
                ),
                ("scheduled_at", models.DateTimeField(db_index=True)),
                ("sent_at", models.DateTimeField(blank=True, null=True)),
                ("error_message", models.TextField(blank=True, default="")),
                ("attempt_count", models.PositiveIntegerField(default=0)),
                ("daily_slot_reserved", models.BooleanField(default=False, editable=False)),
                ("daily_slot_date", models.DateField(blank=True, editable=False, null=True)),
                (
                    "campaign",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="email_messages",
                        to="campaigns.campaign",
                    ),
                ),
                (
                    "lead",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="email_messages",
                        to="leads.lead",
                    ),
                ),
            ],
            options={
                "ordering": ("scheduled_at", "id"),
            },
        ),
        migrations.AddConstraint(
            model_name="emailmessage",
            constraint=models.UniqueConstraint(
                fields=("campaign", "lead"),
                name="email_message_one_per_campaign_lead",
            ),
        ),
        migrations.AddIndex(
            model_name="emailmessage",
            index=models.Index(
                fields=("status", "scheduled_at"), name="email_msg_status_sched_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="emailmessage",
            index=models.Index(
                fields=("campaign", "status"), name="email_msg_campaign_status_idx"
            ),
        ),
    ]
