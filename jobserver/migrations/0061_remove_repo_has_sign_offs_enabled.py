# Generated by Django 4.1.2 on 2022-11-21 15:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("jobserver", "0060_add_project_copilot_notes"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="repo",
            name="has_sign_offs_enabled",
        ),
    ]
