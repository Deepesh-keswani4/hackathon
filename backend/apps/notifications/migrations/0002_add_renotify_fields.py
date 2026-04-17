from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("notifications", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="inappnotification",
            name="requester_email",
            field=models.EmailField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="inappnotification",
            name="renotify_count",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="inappnotification",
            name="last_renotified_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddIndex(
            model_name="inappnotification",
            index=models.Index(fields=["recipient_email", "read"], name="notif_recipient_read_idx"),
        ),
        migrations.AddIndex(
            model_name="inappnotification",
            index=models.Index(fields=["requester_email"], name="notif_requester_idx"),
        ),
    ]
