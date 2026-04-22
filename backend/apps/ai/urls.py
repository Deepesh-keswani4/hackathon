from django.urls import path

from .views import ChatSessionListView, ChatSessionMessagesView, ChatView
from .news_view import NewsFeedView

urlpatterns = [
    path("chat/", ChatView.as_view(), name="ai-chat"),
    path("sessions/", ChatSessionListView.as_view(), name="ai-sessions"),
    path("sessions/<str:session_id>/messages/", ChatSessionMessagesView.as_view(), name="ai-session-messages"),
    path("news/", NewsFeedView.as_view(), name="ai-news"),
]
