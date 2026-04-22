from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from core.permissions import IsEmployee, IsHR, IsManager

from .serializers import (
    AttendanceCheckInSerializer,
    AttendanceLogSerializer,
    AttendancePenaltySerializer,
    AttendancePolicyCreateSerializer,
    AttendancePolicySerializer,
    PenaltyActionSerializer,
    RegularizationApplySerializer,
    RegularizationRejectSerializer,
    RegularizationRequestSerializer,
    WFHApplySerializer,
    WFHRejectSerializer,
    WFHRequestSerializer,
)
from .services import (
    AttendancePenaltyService,
    AttendancePolicyService,
    AttendanceService,
    RegularizationService,
    WFHService,
)


def _error(msg, code="BAD_REQUEST", http_status=400):
    return Response({"error": msg, "code": code, "details": {}}, status=http_status)


# ── Existing ──────────────────────────────────────────────────────────────────

class AttendanceCheckInView(APIView):
    permission_classes = [IsEmployee]

    def post(self, request):
        serializer = AttendanceCheckInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        employee = request.user.employee
        log = AttendanceService(employee).check_in(
            serializer.validated_data["date"],
            serializer.validated_data["status"],
        )
        return Response(AttendanceLogSerializer(log).data)


# ── Regularization ────────────────────────────────────────────────────────────

class RegularizationListView(APIView):
    permission_classes = [IsEmployee]

    def get(self, request):
        employee = request.user.employee
        from .repositories import RegularizationReadRepository
        repo = RegularizationReadRepository()

        if employee.role in ("hr", "admin"):
            items = repo.list()
        elif employee.role in ("manager",):
            items = repo.list(employee__manager_id=employee.id)
        else:
            items = repo.list(employee_id=employee.id)

        return Response(RegularizationRequestSerializer(items, many=True).data)

    def post(self, request):
        serializer = RegularizationApplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        employee = request.user.employee
        svc = RegularizationService(employee)
        try:
            req = svc.apply(
                target_date=serializer.validated_data["date"],
                requested_check_out=serializer.validated_data["requested_check_out"],
                requested_check_in=serializer.validated_data.get("requested_check_in"),
                reason=serializer.validated_data.get("reason", ""),
                applied_by=request.user,
            )
            return Response(RegularizationRequestSerializer(req).data, status=status.HTTP_201_CREATED)
        except (ValueError, PermissionError) as e:
            return _error(str(e))


class RegularizationDetailView(APIView):
    permission_classes = [IsEmployee]

    def _get_req(self, pk):
        from .repositories import RegularizationReadRepository
        return RegularizationReadRepository().get_by_id(pk)

    def get(self, request, pk):
        req = self._get_req(pk)
        if not req:
            return _error("Not found", "NOT_FOUND", 404)
        employee = request.user.employee
        if employee.role not in ("hr", "admin") and req.employee_id != employee.id and req.employee.manager_id != employee.id:
            return _error("Forbidden", "FORBIDDEN", 403)
        return Response(RegularizationRequestSerializer(req).data)

    def delete(self, request, pk):
        req = self._get_req(pk)
        if not req:
            return _error("Not found", "NOT_FOUND", 404)
        employee = request.user.employee
        svc = RegularizationService(employee)
        try:
            req = svc.cancel(req, request.user)
            return Response(RegularizationRequestSerializer(req).data)
        except (ValueError, PermissionError) as e:
            return _error(str(e))


class RegularizationApproveView(APIView):
    permission_classes = [IsManager]

    def post(self, request, pk):
        from .repositories import RegularizationReadRepository
        req = RegularizationReadRepository().get_by_id(pk)
        if not req:
            return _error("Not found", "NOT_FOUND", 404)
        svc = RegularizationService(req.employee)
        try:
            req = svc.approve(req, request.user)
            return Response(RegularizationRequestSerializer(req).data)
        except (ValueError, PermissionError) as e:
            return _error(str(e))


class RegularizationRejectView(APIView):
    permission_classes = [IsManager]

    def post(self, request, pk):
        from .repositories import RegularizationReadRepository
        req = RegularizationReadRepository().get_by_id(pk)
        if not req:
            return _error("Not found", "NOT_FOUND", 404)
        serializer = RegularizationRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        svc = RegularizationService(req.employee)
        try:
            req = svc.reject(req, request.user, serializer.validated_data.get("rejection_reason", ""))
            return Response(RegularizationRequestSerializer(req).data)
        except (ValueError, PermissionError) as e:
            return _error(str(e))


# ── WFH ───────────────────────────────────────────────────────────────────────

class WFHListView(APIView):
    permission_classes = [IsEmployee]

    def get(self, request):
        employee = request.user.employee
        from .repositories import WFHReadRepository
        repo = WFHReadRepository()

        if employee.role in ("hr", "admin"):
            items = repo.list()
        elif employee.role in ("manager",):
            items = repo.list(employee__manager_id=employee.id)
        else:
            items = repo.list(employee_id=employee.id)

        return Response(WFHRequestSerializer(items, many=True).data)

    def post(self, request):
        serializer = WFHApplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        employee = request.user.employee
        svc = WFHService(employee)
        try:
            req = svc.apply(
                dates=serializer.validated_data["dates"],
                reason=serializer.validated_data.get("reason", ""),
                applied_by=request.user,
            )
            return Response(WFHRequestSerializer(req).data, status=status.HTTP_201_CREATED)
        except (ValueError, PermissionError) as e:
            return _error(str(e))


class WFHDetailView(APIView):
    permission_classes = [IsEmployee]

    def _get_req(self, pk):
        from .repositories import WFHReadRepository
        return WFHReadRepository().get_by_id(pk)

    def get(self, request, pk):
        req = self._get_req(pk)
        if not req:
            return _error("Not found", "NOT_FOUND", 404)
        employee = request.user.employee
        if employee.role not in ("hr", "admin") and req.employee_id != employee.id and req.employee.manager_id != employee.id:
            return _error("Forbidden", "FORBIDDEN", 403)
        return Response(WFHRequestSerializer(req).data)

    def delete(self, request, pk):
        req = self._get_req(pk)
        if not req:
            return _error("Not found", "NOT_FOUND", 404)
        employee = request.user.employee
        svc = WFHService(employee)
        try:
            req = svc.cancel(req, request.user)
            return Response(WFHRequestSerializer(req).data)
        except (ValueError, PermissionError) as e:
            return _error(str(e))


class WFHApproveView(APIView):
    permission_classes = [IsManager]

    def post(self, request, pk):
        from .repositories import WFHReadRepository
        req = WFHReadRepository().get_by_id(pk)
        if not req:
            return _error("Not found", "NOT_FOUND", 404)
        svc = WFHService(req.employee)
        try:
            req = svc.approve(req, request.user)
            return Response(WFHRequestSerializer(req).data)
        except (ValueError, PermissionError) as e:
            return _error(str(e))


class WFHRejectView(APIView):
    permission_classes = [IsManager]

    def post(self, request, pk):
        from .repositories import WFHReadRepository
        req = WFHReadRepository().get_by_id(pk)
        if not req:
            return _error("Not found", "NOT_FOUND", 404)
        serializer = WFHRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        svc = WFHService(req.employee)
        try:
            req = svc.reject(req, request.user, serializer.validated_data.get("rejection_reason", ""))
            return Response(WFHRequestSerializer(req).data)
        except (ValueError, PermissionError) as e:
            return _error(str(e))


# ── Penalties ─────────────────────────────────────────────────────────────────

class AttendancePenaltyListView(APIView):
    permission_classes = [IsEmployee]

    def get(self, request):
        employee = request.user.employee
        from .repositories import AttendancePenaltyReadRepository
        repo = AttendancePenaltyReadRepository()

        if employee.role in ("hr", "admin"):
            items = repo.list()
        elif employee.role in ("manager",):
            items = repo.list(employee__manager_id=employee.id)
        else:
            items = repo.list(employee_id=employee.id)

        return Response(AttendancePenaltySerializer(items, many=True).data)


class AttendancePenaltyReverseView(APIView):
    permission_classes = [IsManager]

    def post(self, request, pk):
        from .repositories import AttendancePenaltyReadRepository
        penalty = AttendancePenaltyReadRepository().get_by_id(pk)
        if not penalty:
            return _error("Not found", "NOT_FOUND", 404)
        serializer = PenaltyActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        svc = AttendancePenaltyService()
        try:
            penalty = svc.reverse(penalty, request.user, serializer.validated_data.get("reason", ""))
            return Response(AttendancePenaltySerializer(penalty).data)
        except (ValueError, PermissionError) as e:
            return _error(str(e))


class AttendancePenaltyWaiveView(APIView):
    permission_classes = [IsHR]

    def post(self, request, pk):
        from .repositories import AttendancePenaltyReadRepository
        penalty = AttendancePenaltyReadRepository().get_by_id(pk)
        if not penalty:
            return _error("Not found", "NOT_FOUND", 404)
        serializer = PenaltyActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        svc = AttendancePenaltyService()
        try:
            penalty = svc.waive(penalty, request.user, serializer.validated_data.get("reason", ""))
            return Response(AttendancePenaltySerializer(penalty).data)
        except (ValueError, PermissionError) as e:
            return _error(str(e))


# ── Policy ────────────────────────────────────────────────────────────────────

class AttendancePolicyView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsHR()]
        return [IsEmployee()]

    def get(self, request):
        svc = AttendancePolicyService()
        policy = svc.get_active()
        if not policy:
            return Response(svc.get_active_or_default())
        return Response(AttendancePolicySerializer(policy).data)

    def post(self, request):
        serializer = AttendancePolicyCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        svc = AttendancePolicyService()
        policy = svc.create_version(serializer.validated_data, request.user)
        return Response(AttendancePolicySerializer(policy).data, status=status.HTTP_201_CREATED)


class AttendancePolicyHistoryView(APIView):
    permission_classes = [IsHR]

    def get(self, request):
        from .repositories import AttendancePolicyReadRepository
        items = AttendancePolicyReadRepository().list_all()
        return Response(AttendancePolicySerializer(items, many=True).data)
