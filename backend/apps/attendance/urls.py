from django.urls import path

from .views import (
    AttendanceCheckInView,
    AttendancePenaltyListView,
    AttendancePenaltyReverseView,
    AttendancePenaltyWaiveView,
    AttendancePolicyHistoryView,
    AttendancePolicyView,
    RegularizationApproveView,
    RegularizationDetailView,
    RegularizationListView,
    RegularizationRejectView,
    WFHApproveView,
    WFHDetailView,
    WFHListView,
    WFHRejectView,
)

urlpatterns = [
    # Existing
    path("check-in/", AttendanceCheckInView.as_view(), name="attendance-check-in"),

    # Regularization
    path("regularization/", RegularizationListView.as_view(), name="regularization-list"),
    path("regularization/<int:pk>/", RegularizationDetailView.as_view(), name="regularization-detail"),
    path("regularization/<int:pk>/approve/", RegularizationApproveView.as_view(), name="regularization-approve"),
    path("regularization/<int:pk>/reject/", RegularizationRejectView.as_view(), name="regularization-reject"),

    # WFH
    path("wfh/", WFHListView.as_view(), name="wfh-list"),
    path("wfh/<int:pk>/", WFHDetailView.as_view(), name="wfh-detail"),
    path("wfh/<int:pk>/approve/", WFHApproveView.as_view(), name="wfh-approve"),
    path("wfh/<int:pk>/reject/", WFHRejectView.as_view(), name="wfh-reject"),

    # Penalties
    path("penalties/", AttendancePenaltyListView.as_view(), name="penalty-list"),
    path("penalties/<int:pk>/reverse/", AttendancePenaltyReverseView.as_view(), name="penalty-reverse"),
    path("penalties/<int:pk>/waive/", AttendancePenaltyWaiveView.as_view(), name="penalty-waive"),

    # Policy
    path("policy/", AttendancePolicyView.as_view(), name="attendance-policy"),
    path("policy/history/", AttendancePolicyHistoryView.as_view(), name="attendance-policy-history"),
]
