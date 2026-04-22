from __future__ import annotations

from core.repositories.base import BaseReadRepository, BaseWriteRepository

from .models import (
    AttendanceAnomaly,
    AttendanceLog,
    AttendancePenalty,
    AttendancePolicy,
    RegularizationRequest,
    WFHRequest,
)


class AttendanceLogReadRepository(BaseReadRepository[AttendanceLog]):
    def get_by_id(self, id: int) -> AttendanceLog | None:
        return AttendanceLog.objects.select_related("employee", "employee__user").filter(pk=id).first()

    def list(self, **filters) -> list[AttendanceLog]:
        return list(AttendanceLog.objects.filter(**filters).select_related("employee", "employee__user"))

    def get_by_employee_and_date(self, employee_id: int, date) -> AttendanceLog | None:
        return AttendanceLog.objects.filter(employee_id=employee_id, date=date).first()


class AttendanceLogWriteRepository(BaseWriteRepository[AttendanceLog]):
    def create(self, **kwargs) -> AttendanceLog:
        return AttendanceLog.objects.create(**kwargs)

    def update(self, instance: AttendanceLog, **kwargs) -> AttendanceLog:
        for key, value in kwargs.items():
            setattr(instance, key, value)
        instance.save(update_fields=list(kwargs.keys()) + ["updated_at"])
        return instance

    def delete(self, instance: AttendanceLog) -> None:
        instance.delete()


class AttendanceAnomalyWriteRepository(BaseWriteRepository[AttendanceAnomaly]):
    def create(self, **kwargs) -> AttendanceAnomaly:
        return AttendanceAnomaly.objects.create(**kwargs)

    def update(self, instance: AttendanceAnomaly, **kwargs) -> AttendanceAnomaly:
        for key, value in kwargs.items():
            setattr(instance, key, value)
        instance.save(update_fields=list(kwargs.keys()))
        return instance

    def delete(self, instance: AttendanceAnomaly) -> None:
        instance.delete()


# ── Regularization ────────────────────────────────────────────────────────────

class RegularizationReadRepository(BaseReadRepository[RegularizationRequest]):
    def get_by_id(self, id: int) -> RegularizationRequest | None:
        return (
            RegularizationRequest.objects
            .select_related("employee__user", "employee__manager__user", "applied_by", "reviewed_by")
            .filter(pk=id)
            .first()
        )

    def list(self, **filters) -> list[RegularizationRequest]:  # noqa: D102
        return list(
            RegularizationRequest.objects
            .select_related("employee__user", "applied_by", "reviewed_by")
            .filter(**filters)
            .order_by("-created_at")
        )

    def count_attempts(self, employee_id: int, date) -> int:
        return RegularizationRequest.objects.filter(employee_id=employee_id, date=date).count()

    def get_active_for_date(self, employee_id: int, date) -> RegularizationRequest | None:
        """Returns PENDING or APPROVED request for date (blocks penalty)."""
        return RegularizationRequest.objects.filter(
            employee_id=employee_id,
            date=date,
            status__in=[RegularizationRequest.STATUS_PENDING, RegularizationRequest.STATUS_APPROVED],
        ).first()


class RegularizationWriteRepository(BaseWriteRepository[RegularizationRequest]):
    def create(self, **kwargs) -> RegularizationRequest:
        return RegularizationRequest.objects.create(**kwargs)

    def update(self, instance: RegularizationRequest, **kwargs) -> RegularizationRequest:
        for key, value in kwargs.items():
            setattr(instance, key, value)
        instance.save(update_fields=list(kwargs.keys()) + ["updated_at"])
        return instance

    def delete(self, instance: RegularizationRequest) -> None:
        instance.delete()


# ── WFH ───────────────────────────────────────────────────────────────────────

class WFHReadRepository(BaseReadRepository[WFHRequest]):
    def get_by_id(self, id: int) -> WFHRequest | None:
        return (
            WFHRequest.objects
            .select_related("employee__user", "employee__manager__user", "applied_by", "reviewed_by")
            .filter(pk=id)
            .first()
        )

    def list(self, **filters) -> list[WFHRequest]:
        return list(
            WFHRequest.objects
            .select_related("employee__user", "applied_by", "reviewed_by")
            .filter(**filters)
            .order_by("-created_at")
        )

    def get_approved_for_date(self, employee_id: int, date_str: str) -> WFHRequest | None:
        """Returns approved WFH request that covers date_str (ISO format)."""
        return WFHRequest.objects.filter(
            employee_id=employee_id,
            status=WFHRequest.STATUS_APPROVED,
            dates__contains=date_str,
        ).first()

    def get_pending_or_approved_for_date(self, employee_id: int, date_str: str) -> WFHRequest | None:
        return WFHRequest.objects.filter(
            employee_id=employee_id,
            status__in=[WFHRequest.STATUS_PENDING, WFHRequest.STATUS_APPROVED],
            dates__contains=date_str,
        ).first()


class WFHWriteRepository(BaseWriteRepository[WFHRequest]):
    def create(self, **kwargs) -> WFHRequest:
        return WFHRequest.objects.create(**kwargs)

    def update(self, instance: WFHRequest, **kwargs) -> WFHRequest:
        for key, value in kwargs.items():
            setattr(instance, key, value)
        instance.save(update_fields=list(kwargs.keys()) + ["updated_at"])
        return instance

    def delete(self, instance: WFHRequest) -> None:
        instance.delete()


# ── Penalty ───────────────────────────────────────────────────────────────────

class AttendancePenaltyReadRepository(BaseReadRepository[AttendancePenalty]):
    def get_by_id(self, id: int) -> AttendancePenalty | None:
        return AttendancePenalty.objects.select_related("employee__user", "reversed_by").filter(pk=id).first()

    def list(self, **filters) -> list[AttendancePenalty]:
        return list(
            AttendancePenalty.objects
            .select_related("employee__user", "reversed_by")
            .filter(**filters)
            .order_by("-date")
        )

    def has_active_penalty(self, employee_id: int, date) -> bool:
        return AttendancePenalty.objects.filter(
            employee_id=employee_id, date=date, status=AttendancePenalty.STATUS_ACTIVE
        ).exists()


class AttendancePenaltyWriteRepository(BaseWriteRepository[AttendancePenalty]):
    def create(self, **kwargs) -> AttendancePenalty:
        return AttendancePenalty.objects.create(**kwargs)

    def update(self, instance: AttendancePenalty, **kwargs) -> AttendancePenalty:
        for key, value in kwargs.items():
            setattr(instance, key, value)
        instance.save(update_fields=list(kwargs.keys()))
        return instance

    def delete(self, instance: AttendancePenalty) -> None:
        instance.delete()


# ── Policy ────────────────────────────────────────────────────────────────────

class AttendancePolicyReadRepository(BaseReadRepository[AttendancePolicy]):
    def get_by_id(self, id: int) -> AttendancePolicy | None:
        return AttendancePolicy.objects.filter(pk=id).first()

    def list(self, **filters) -> list[AttendancePolicy]:
        return list(AttendancePolicy.objects.filter(**filters).order_by("-version"))

    def get_active(self) -> AttendancePolicy | None:
        return AttendancePolicy.objects.filter(is_active=True).order_by("-version").first()

    def list_all(self) -> list[AttendancePolicy]:
        return list(AttendancePolicy.objects.all().order_by("-version"))


class AttendancePolicyWriteRepository(BaseWriteRepository[AttendancePolicy]):
    def create(self, **kwargs) -> AttendancePolicy:
        return AttendancePolicy.objects.create(**kwargs)

    def update(self, instance: AttendancePolicy, **kwargs) -> AttendancePolicy:
        for key, value in kwargs.items():
            setattr(instance, key, value)
        instance.save(update_fields=list(kwargs.keys()))
        return instance

    def delete(self, instance: AttendancePolicy) -> None:
        instance.delete()
