# Generated by Django 3.2.5 on 2021-09-20 09:53

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("jobserver", "0068_remove_v1_onboarding_fields_and_models"),
    ]

    operations = [
        migrations.AddField(
            model_name="org",
            name="created_by",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="created_orgs",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="project",
            name="created_by",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="created_projects",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
