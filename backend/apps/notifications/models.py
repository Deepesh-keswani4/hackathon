from django.db import models


class InAppNotification(models.Model):
    recipient_email = models.EmailField()
    subject = models.CharField(max_length=200)
    body = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # Re-notify support: employee who triggered this notification can request a re-push
    requester_email = models.EmailField(blank=True, default="")
    renotify_count = models.PositiveSmallIntegerField(default=0)
    last_renotified_at = models.DateTimeField(null=True, blank=True)

    RENOTIFY_MAX = 3
    RENOTIFY_COOLDOWN_MINUTES = 60

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient_email", "read"]),
            models.Index(fields=["requester_email"]),
        ]

    def __str__(self) -> str:
        return f"Notification {self.recipient_email} {self.subject}"
