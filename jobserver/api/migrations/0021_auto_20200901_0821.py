# Generated by Django 3.0.7 on 2020-09-01 08:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0020_job_force_run_dependencies"),
    ]

    operations = [
        migrations.RenameField(
            model_name="job",
            old_name="operation",
            new_name="action",
        ),
    ]
