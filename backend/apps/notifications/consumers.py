"""
NotificationConsumer — WebSocket endpoint: ws/notifications/?token=<JWT>

On connect  : authenticate via JWT, join personal group, flush unread notifications.
On message  : mark notification read (client sends {"type": "mark_read", "id": N}).
Push events : channel layer sends {"type": "notify", ...} → forwarded to client.
"""
import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger("hrms")


def _channel_group(user_id: int) -> str:
    return f"notifications_{user_id}"


class NotificationConsumer(AsyncWebsocketConsumer):

    # ── Lifecycle ────────────────────────────────────────────────────────────

    async def connect(self):
        user = await self._authenticate()
        if not user:
            await self.close(code=4001)
            return

        self.user = user
        self.group = _channel_group(user.pk)

        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

        # Flush unread notifications on connect
        await self._send_unread()
        logger.info("WS connect user_id=%s", user.pk)

    async def disconnect(self, code):
        if hasattr(self, "group"):
            await self.channel_layer.group_discard(self.group, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data or "{}")
        except json.JSONDecodeError:
            return

        if data.get("type") == "mark_read":
            await self._mark_read(data.get("id"))

    # ── Channel layer handler — called by group_send ─────────────────────────

    async def notify(self, event):
        """Forward a notification pushed via channel layer to the WS client."""
        await self.send(text_data=json.dumps({
            "type":     "notification",
            "id":       event.get("id"),
            "subject":  event.get("subject"),
            "body":     event.get("body"),
            "metadata": event.get("metadata", {}),
            "created_at": event.get("created_at"),
        }))

    # ── Helpers ──────────────────────────────────────────────────────────────

    async def _authenticate(self):
        """Validate JWT from query-string; return User or None."""
        from channels.db import database_sync_to_async
        from urllib.parse import parse_qs

        qs = parse_qs(self.scope.get("query_string", b"").decode())
        token = (qs.get("token") or [""])[0]
        if not token:
            return None

        @database_sync_to_async
        def _get_user(raw_token):
            try:
                from rest_framework_simplejwt.tokens import AccessToken
                from django.contrib.auth import get_user_model
                User = get_user_model()
                payload = AccessToken(raw_token)
                user = User.objects.filter(pk=payload["user_id"]).first()
                if not user:
                    logger.warning("WS auth: user_id=%s not found", payload["user_id"])
                return user
            except Exception as exc:
                logger.warning("WS auth failed: %s", exc)
                return None

        return await _get_user(token)

    async def _send_unread(self):
        """Send up to 20 unread notifications on connect."""
        from channels.db import database_sync_to_async

        @database_sync_to_async
        def _fetch():
            from apps.notifications.models import InAppNotification
            return list(
                InAppNotification.objects.filter(
                    recipient_email=self.user.email, read=False
                ).order_by("-created_at")[:20]
            )

        notifications = await _fetch()
        for n in reversed(notifications):  # oldest first
            await self.send(text_data=json.dumps({
                "type":       "notification",
                "id":         n.pk,
                "subject":    n.subject,
                "body":       n.body,
                "metadata":   n.metadata,
                "created_at": n.created_at.isoformat(),
            }))

    async def _mark_read(self, notification_id):
        if not notification_id:
            return
        from channels.db import database_sync_to_async

        @database_sync_to_async
        def _do():
            from apps.notifications.models import InAppNotification
            InAppNotification.objects.filter(
                pk=notification_id, recipient_email=self.user.email
            ).update(read=True)

        await _do()
