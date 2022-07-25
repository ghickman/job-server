# Generated by Django 4.0.6 on 2022-07-25 10:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("jobserver", "0029_add_missing_releasefile_constraint"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="releasefile",
            name="jobserver_releasefile_deleted_fields_both_set",
        ),
        migrations.RemoveConstraint(
            model_name="user",
            name="jobserver_user_both_pat_expires_at_and_pat_token_set",
        ),
        migrations.AddConstraint(
            model_name="releasefile",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(
                        ("deleted_at__isnull", True), ("deleted_by__isnull", True)
                    ),
                    models.Q(
                        ("deleted_at__isnull", False), ("deleted_by__isnull", False)
                    ),
                    _connector="OR",
                ),
                name="jobserver_releasefile_deleted_fields_both_set",
            ),
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(
                        ("pat_expires_at__isnull", True), ("pat_token__isnull", True)
                    ),
                    models.Q(
                        ("pat_expires_at__isnull", False), ("pat_token__isnull", False)
                    ),
                    _connector="OR",
                ),
                name="jobserver_user_both_pat_expires_at_and_pat_token_set",
            ),
        ),
    ]
