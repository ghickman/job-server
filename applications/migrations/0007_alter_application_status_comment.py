# Generated by Django 3.2.10 on 2021-12-22 14:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("applications", "0006_add_researcher_daa_and_github_username"),
    ]

    operations = [
        migrations.AlterField(
            model_name="application",
            name="status_comment",
            field=models.TextField(blank=True, default=""),
        ),
    ]
