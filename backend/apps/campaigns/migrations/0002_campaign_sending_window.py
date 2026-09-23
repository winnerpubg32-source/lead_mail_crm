# Generated manually for Phase 7 SMTP scheduling.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("campaigns", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="campaign",
            name="sending_start_time",
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="campaign",
            name="sending_end_time",
            field=models.TimeField(blank=True, null=True),
        ),
    ]
