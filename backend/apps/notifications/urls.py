from django.urls import path

from .views import (
    NotificationListView,
    NotificationMarkAllReadView,
    NotificationMarkReadView,
    NotificationRenotifyView,
    NotificationUnreadCountView,
)

urlpatterns = [
    path("", NotificationListView.as_view(), name="notifications-list"),
    path("unread-count/", NotificationUnreadCountView.as_view(), name="notifications-unread-count"),
    path("read-all/", NotificationMarkAllReadView.as_view(), name="notifications-mark-all-read"),
    path("renotify/", NotificationRenotifyView.as_view(), name="notifications-renotify"),
    path("<int:notification_id>/read/", NotificationMarkReadView.as_view(), name="notification-mark-read"),
]
