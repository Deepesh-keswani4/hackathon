import logging
from datetime import timedelta

from django.utils import timezone

from .models import InAppNotification

logger = logging.getLogger("hrms")


class InAppNotificationService:
    def create_notification(
        self,
        recipient_email: str,
        subject: str,
        body: str,
        metadata: dict,
        requester_email: str = "",
    ) -> InAppNotification:
        notification = InAppNotification.objects.create(
            recipient_email=recipient_email,
            subject=subject,
            body=body,
            metadata=metadata or {},
            requester_email=requester_email or "",
        )
        logger.info("In-app notification saved id=%s recipient=%s", notification.id, recipient_email)
        self._push_to_websocket(notification)
        return notification

    def push_notification_ws(self, notification: InAppNotification, extra_subject_prefix: str = "") -> bool:
        """Re-push an existing notification to the recipient's WS group."""
        return self._push_to_websocket(notification, subject_override=(extra_subject_prefix + notification.subject) if extra_subject_prefix else None)

    def renotify_leave(self, requester_email: str, leave_id: int) -> dict:
        """
        Re-notify manager about a pending leave request.

        States:
          re_pushed     — manager hasn't read yet; re-pushed same notification
          new_reminder  — manager read but leave still PENDING; new notification created
          limit_reached — renotify_count >= RENOTIFY_MAX
          cooldown      — called too recently; returns minutes until next allowed
          not_found     — no pending leave / no manager notification found
        """
        from apps.leaves.models import LeaveRequest
        from apps.employees.models import Employee

        # Verify leave exists, belongs to requester, is PENDING
        try:
            employee = Employee.objects.select_related("user", "manager__user").filter(
                user__email=requester_email
            ).first()
            if not employee:
                return {"status": "not_found", "error": "Employee not found"}

            leave = LeaveRequest.objects.filter(
                pk=leave_id,
                employee=employee,
                status=LeaveRequest.STATUS_PENDING,
            ).first()
            if not leave:
                return {"status": "not_found", "error": "Pending leave not found"}

            manager = employee.manager
            if not manager or not manager.user:
                return {"status": "not_found", "error": "Manager not found"}

            manager_email = manager.user.email
        except Exception as exc:
            logger.exception("renotify_leave lookup failed leave_id=%s", leave_id)
            return {"status": "error", "error": str(exc)}

        # Find manager's notification for this leave
        notif = (
            InAppNotification.objects.filter(
                recipient_email=manager_email,
                requester_email=requester_email,
            )
            .filter(metadata__leave_id=leave_id)
            .order_by("-created_at")
            .first()
        )
        if not notif:
            # Fallback: find by recipient + leave_id without requester_email (older records)
            notif = (
                InAppNotification.objects.filter(recipient_email=manager_email)
                .filter(metadata__leave_id=leave_id)
                .order_by("-created_at")
                .first()
            )
        if not notif:
            return {"status": "not_found", "error": "Manager notification not found for this leave"}

        # Limit check
        if notif.renotify_count >= InAppNotification.RENOTIFY_MAX:
            return {
                "status": "limit_reached",
                "renotify_count": notif.renotify_count,
                "manager_read": notif.read,
            }

        # Cooldown check
        if notif.last_renotified_at:
            elapsed = timezone.now() - notif.last_renotified_at
            cooldown = timedelta(minutes=InAppNotification.RENOTIFY_COOLDOWN_MINUTES)
            if elapsed < cooldown:
                remaining = int((cooldown - elapsed).total_seconds() / 60) + 1
                return {
                    "status": "cooldown",
                    "next_available_in_minutes": remaining,
                    "manager_read": notif.read,
                }

        now = timezone.now()

        if not notif.read:
            # Manager hasn't read yet — re-push same notification with reminder prefix
            self.push_notification_ws(notif, extra_subject_prefix="🔁 Reminder: ")
            notif.renotify_count += 1
            notif.last_renotified_at = now
            notif.save(update_fields=["renotify_count", "last_renotified_at"])
            logger.info("Re-pushed unread notification id=%s leave_id=%s count=%s", notif.pk, leave_id, notif.renotify_count)
            return {
                "status": "re_pushed",
                "manager_read": False,
                "renotify_count": notif.renotify_count,
                "reminders_left": InAppNotification.RENOTIFY_MAX - notif.renotify_count,
            }
        else:
            # Manager read it but hasn't acted — create fresh reminder
            reminder = self.create_notification(
                recipient_email=manager_email,
                subject=f"🔁 Reminder #{notif.renotify_count + 1}: {notif.subject}",
                body=(
                    f"This is a follow-up reminder.\n\n{notif.body}\n\n"
                    f"This leave request is still pending your action."
                ),
                metadata={**notif.metadata, "is_reminder": True, "reminder_count": notif.renotify_count + 1},
                requester_email=requester_email,
            )
            notif.renotify_count += 1
            notif.last_renotified_at = now
            notif.save(update_fields=["renotify_count", "last_renotified_at"])
            logger.info("Sent new reminder notification id=%s leave_id=%s count=%s", reminder.pk, leave_id, notif.renotify_count)
            return {
                "status": "new_reminder",
                "manager_read": True,
                "renotify_count": notif.renotify_count,
                "reminders_left": InAppNotification.RENOTIFY_MAX - notif.renotify_count,
            }

    def _push_to_websocket(self, notification: InAppNotification, subject_override: str | None = None) -> bool:
        """Push notification to the recipient's WebSocket group via channel layer (best-effort)."""
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.filter(email=notification.recipient_email).only("id").first()
            if not user:
                return False

            from asgiref.sync import async_to_sync
            from channels.layers import get_channel_layer

            channel_layer = get_channel_layer()
            if not channel_layer:
                return False

            async_to_sync(channel_layer.group_send)(
                f"notifications_{user.pk}",
                {
                    "type":       "notify",
                    "id":         notification.pk,
                    "subject":    subject_override or notification.subject,
                    "body":       notification.body,
                    "metadata":   notification.metadata,
                    "created_at": notification.created_at.isoformat(),
                },
            )
            return True
        except Exception:
            logger.exception("Failed to push WS notification id=%s", notification.pk)
            return False
