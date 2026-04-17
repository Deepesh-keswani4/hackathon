from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsEmployee
from core.utils import error_response

from .models import InAppNotification
from .serializers import InAppNotificationSerializer
from .services import InAppNotificationService


class NotificationListView(APIView):
    permission_classes = [IsEmployee]

    def get(self, request):
        limit = min(int(request.query_params.get("limit", 50)), 100)
        unread_only = request.query_params.get("unread") == "true"
        qs = InAppNotification.objects.filter(recipient_email=request.user.email).order_by("-created_at")
        if unread_only:
            qs = qs.filter(read=False)
        return Response(InAppNotificationSerializer(qs[:limit], many=True).data)


class NotificationMarkReadView(APIView):
    permission_classes = [IsEmployee]

    def post(self, request, notification_id: int):
        notif = InAppNotification.objects.filter(pk=notification_id, recipient_email=request.user.email).first()
        if not notif:
            return Response(error_response("Notification not found", "NOT_FOUND"), status=404)
        notif.read = True
        notif.save(update_fields=["read"])
        return Response({"id": notif.pk, "read": True})


class NotificationMarkAllReadView(APIView):
    permission_classes = [IsEmployee]

    def post(self, request):
        updated = InAppNotification.objects.filter(recipient_email=request.user.email, read=False).update(read=True)
        return Response({"marked_read": updated})


class NotificationUnreadCountView(APIView):
    permission_classes = [IsEmployee]

    def get(self, request):
        count = InAppNotification.objects.filter(recipient_email=request.user.email, read=False).count()
        return Response({"unread_count": count})


class NotificationRenotifyView(APIView):
    """
    POST /api/notifications/renotify/
    Body: {"leave_id": <int>}

    Employee re-notifies manager about a pending leave.
    - Manager unread  → re-push same notification to manager's WS
    - Manager read    → create fresh reminder notification
    - Limit (3)       → blocked
    - Cooldown (60m)  → blocked with next_available_in_minutes
    """
    permission_classes = [IsEmployee]

    def post(self, request):
        leave_id = request.data.get("leave_id")
        if not leave_id:
            return Response(
                error_response("leave_id is required", "INVALID_INPUT"),
                status=400,
            )
        try:
            leave_id = int(leave_id)
        except (TypeError, ValueError):
            return Response(
                error_response("leave_id must be an integer", "INVALID_INPUT"),
                status=400,
            )

        result = InAppNotificationService().renotify_leave(
            requester_email=request.user.email,
            leave_id=leave_id,
        )

        if result.get("status") == "error":
            return Response(error_response(result["error"], "RENOTIFY_ERROR"), status=500)
        if result.get("status") == "not_found":
            return Response(error_response(result.get("error", "Not found"), "NOT_FOUND"), status=404)

        return Response(result, status=200)
