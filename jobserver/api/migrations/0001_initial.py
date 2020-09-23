# Generated by Django 3.0.7 on 2020-06-06 08:10

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Job",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("repo", models.CharField(db_index=True, max_length=300)),
                ("tag", models.CharField(max_length=200)),
                ("acked", models.BooleanField(default=False)),
                ("operation", models.CharField(max_length=20)),
                ("status_code", models.IntegerField(blank=True, null=True)),
                ("output_url", models.CharField(blank=True, max_length=100, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
            ],
        ),
    ]
