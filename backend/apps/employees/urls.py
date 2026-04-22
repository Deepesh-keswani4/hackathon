from django.urls import path

from .views import EmployeeDetailView, EmployeeListCreateView, MeView, TeamStatusView

urlpatterns = [
    path("",              EmployeeListCreateView.as_view(), name="employee-list-create"),
    path("me/",           MeView.as_view(),                 name="employee-me"),
    path("team-status/",  TeamStatusView.as_view(),         name="employee-team-status"),
    path("<int:pk>/",     EmployeeDetailView.as_view(),     name="employee-detail"),
]
