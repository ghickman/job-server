# Generated by Django 4.1.2 on 2023-01-20 10:39

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models

import jobserver.models.common


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("jobserver", "0005_add_report"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("interactive", "0004_delete_analysisrequest"),
    ]

    operations = [
        migrations.CreateModel(
            name="AnalysisRequest",
            fields=[
                (
                    "id",
                    models.CharField(
                        default=jobserver.models.common.new_ulid_str,
                        editable=False,
                        max_length=26,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("title", models.TextField()),
                ("codelist_slug", models.TextField()),
                ("codelist_name", models.TextField()),
                ("start_date", models.DateField()),
                ("end_date", models.DateField()),
                ("commit_sha", models.TextField()),
                ("complete_email_sent_at", models.DateTimeField(null=True)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="analysis_requests",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "job_request",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="analysis_request",
                        to="jobserver.jobrequest",
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="analysis_requests",
                        to="jobserver.project",
                    ),
                ),
                (
                    "report",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="analysis_requests",
                        to="jobserver.report",
                    ),
                ),
            ],
        ),
    ]
