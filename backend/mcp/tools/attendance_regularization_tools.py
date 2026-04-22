"""
MCP tools for attendance regularization, WFH, penalties, and policy.
All write operations go through the service layer — never touch ORM directly.
"""

import logging
from datetime import date, timedelta

from mcp.rbac import ensure_role
from mcp.registry import tool

logger = logging.getLogger("hrms")


def _parse_date(val) -> date | None:
    if isinstance(val, date):
        return val
    if not val:
        return None
    try:
        return date.fromisoformat(str(val))
    except Exception:
        return None


# ── Regularization ────────────────────────────────────────────────────────────

@tool("create_regularization_request")
def create_regularization_request(
    employee_id: int, requester_id: int, requester_role: str, input_data: dict | None = None
) -> dict:
    err = ensure_role(requester_role, ["employee", "manager", "hr", "admin"])
    if err:
        return err

    data = input_data or {}
    target_date = _parse_date(data.get("date"))
    check_out_str = data.get("requested_check_out") or data.get("check_out")
    check_in_str = data.get("requested_check_in") or data.get("check_in")

    if not target_date:
        return {"error": "date is required (YYYY-MM-DD)", "code": "INVALID_INPUT"}
    if not check_out_str:
        return {"error": "requested_check_out is required", "code": "INVALID_INPUT"}

    try:
        from datetime import time as time_type
        check_out = time_type.fromisoformat(str(check_out_str))
        check_in = time_type.fromisoformat(str(check_in_str)) if check_in_str else None
    except Exception:
        return {"error": "Invalid time format. Use HH:MM or HH:MM:SS", "code": "INVALID_INPUT"}

    try:
        from apps.employees.models import Employee
        from django.contrib.auth import get_user_model
        User = get_user_model()

        employee = Employee.objects.filter(pk=employee_id).first()
        if not employee:
            return {"error": "Employee not found", "code": "NOT_FOUND"}

        requester_user = User.objects.filter(employee__id=requester_id).first()

        from apps.attendance.services import RegularizationService
        svc = RegularizationService(employee)
        req = svc.apply(
            target_date=target_date,
            requested_check_out=check_out,
            requested_check_in=check_in,
            reason=data.get("reason", ""),
            applied_by=requester_user,
        )
        logger.info("MCP tool ok tool=create_regularization_request id=%s", req.pk)
        return {
            "regularization_request": {
                "id": req.pk,
                "date": str(req.date),
                "requested_check_in": str(req.requested_check_in) if req.requested_check_in else None,
                "requested_check_out": str(req.requested_check_out),
                "status": req.status,
                "attempt_number": req.attempt_number,
            }
        }
    except ValueError as e:
        return {"error": str(e), "code": "VALIDATION_ERROR"}
    except Exception as e:
        logger.exception("MCP tool error tool=create_regularization_request")
        return {"error": str(e), "code": "SERVER_ERROR"}


@tool("get_regularization_requests")
def get_regularization_requests(
    employee_id: int, requester_id: int, requester_role: str, input_data: dict | None = None
) -> dict:
    err = ensure_role(requester_role, ["employee", "manager", "hr", "admin"])
    if err:
        return err

    data = input_data or {}
    try:
        from apps.attendance.models import RegularizationRequest

        qs = RegularizationRequest.objects.select_related("employee__user").order_by("-created_at")

        if requester_role == "employee":
            qs = qs.filter(employee_id=employee_id)
        elif requester_role == "manager":
            from apps.employees.models import Employee
            manager = Employee.objects.filter(pk=requester_id).first()
            if manager:
                qs = qs.filter(employee__manager_id=manager.id)
        # hr/admin see all

        status_filter = data.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter.upper())

        items = list(qs[:30].values(
            "id", "date", "requested_check_in", "requested_check_out",
            "reason", "status", "rejection_reason", "attempt_number",
            "penalty_reversed", "created_at",
        ))
        for item in items:
            item["date"] = str(item["date"])
            item["created_at"] = str(item["created_at"])

        logger.info("MCP tool ok tool=get_regularization_requests count=%s", len(items))
        return {"regularization_requests": items}
    except Exception as e:
        logger.exception("MCP tool error tool=get_regularization_requests")
        return {"error": str(e), "code": "SERVER_ERROR"}


@tool("approve_regularization_request")
def approve_regularization_request(
    employee_id: int, requester_id: int, requester_role: str, input_data: dict | None = None
) -> dict:
    err = ensure_role(requester_role, ["manager", "hr", "admin"])
    if err:
        return err

    data = input_data or {}
    reg_id = data.get("regularization_id") or data.get("id")
    if not reg_id:
        return {"error": "regularization_id is required", "code": "INVALID_INPUT"}

    try:
        from apps.attendance.models import RegularizationRequest
        from apps.attendance.services import RegularizationService
        from django.contrib.auth import get_user_model
        User = get_user_model()

        req = RegularizationRequest.objects.select_related("employee").filter(pk=reg_id).first()
        if not req:
            return {"error": f"Regularization request #{reg_id} not found", "code": "NOT_FOUND"}

        approver = User.objects.filter(employee__id=requester_id).first()
        svc = RegularizationService(req.employee)
        req = svc.approve(req, approver)

        logger.info("MCP tool ok tool=approve_regularization_request id=%s", req.pk)
        return {
            "approved": True,
            "regularization_id": req.pk,
            "date": str(req.date),
            "penalty_reversed": req.penalty_reversed,
            "status": req.status,
        }
    except (ValueError, PermissionError) as e:
        return {"error": str(e), "code": "VALIDATION_ERROR"}
    except Exception as e:
        logger.exception("MCP tool error tool=approve_regularization_request")
        return {"error": str(e), "code": "SERVER_ERROR"}


@tool("reject_regularization_request")
def reject_regularization_request(
    employee_id: int, requester_id: int, requester_role: str, input_data: dict | None = None
) -> dict:
    err = ensure_role(requester_role, ["manager", "hr", "admin"])
    if err:
        return err

    data = input_data or {}
    reg_id = data.get("regularization_id") or data.get("id")
    if not reg_id:
        return {"error": "regularization_id is required", "code": "INVALID_INPUT"}

    try:
        from apps.attendance.models import RegularizationRequest
        from apps.attendance.services import RegularizationService
        from django.contrib.auth import get_user_model
        User = get_user_model()

        req = RegularizationRequest.objects.select_related("employee").filter(pk=reg_id).first()
        if not req:
            return {"error": f"Regularization request #{reg_id} not found", "code": "NOT_FOUND"}

        approver = User.objects.filter(employee__id=requester_id).first()
        svc = RegularizationService(req.employee)
        req = svc.reject(req, approver, data.get("rejection_reason", ""))

        logger.info("MCP tool ok tool=reject_regularization_request id=%s", req.pk)
        return {"rejected": True, "regularization_id": req.pk, "status": req.status}
    except (ValueError, PermissionError) as e:
        return {"error": str(e), "code": "VALIDATION_ERROR"}
    except Exception as e:
        logger.exception("MCP tool error tool=reject_regularization_request")
        return {"error": str(e), "code": "SERVER_ERROR"}


# ── WFH ───────────────────────────────────────────────────────────────────────

@tool("create_wfh_request")
def create_wfh_request(
    employee_id: int, requester_id: int, requester_role: str, input_data: dict | None = None
) -> dict:
    err = ensure_role(requester_role, ["employee", "manager", "hr", "admin"])
    if err:
        return err

    data = input_data or {}

    # Accept dates list OR from_date+to_date
    dates = data.get("dates") or []
    from_date = _parse_date(data.get("from_date"))
    to_date = _parse_date(data.get("to_date"))

    if not dates and from_date and to_date:
        current = from_date
        while current <= to_date:
            if current.weekday() < 5:
                dates.append(current.isoformat())
            current += timedelta(days=1)
    elif not dates:
        return {"error": "Provide 'dates' list or 'from_date'+'to_date'", "code": "INVALID_INPUT"}

    # Normalize to ISO strings
    normalized = []
    for d in dates:
        parsed = _parse_date(d)
        if parsed:
            normalized.append(parsed.isoformat())
    if not normalized:
        return {"error": "No valid dates provided", "code": "INVALID_INPUT"}

    try:
        from apps.employees.models import Employee
        from django.contrib.auth import get_user_model
        User = get_user_model()

        employee = Employee.objects.filter(pk=employee_id).first()
        if not employee:
            return {"error": "Employee not found", "code": "NOT_FOUND"}

        requester_user = User.objects.filter(employee__id=requester_id).first()

        from apps.attendance.services import WFHService
        svc = WFHService(employee)
        req = svc.apply(
            dates=normalized,
            reason=data.get("reason", ""),
            applied_by=requester_user,
        )
        logger.info("MCP tool ok tool=create_wfh_request id=%s dates=%s", req.pk, len(req.dates))
        return {
            "wfh_request": {
                "id": req.pk,
                "dates": req.dates,
                "dates_count": len(req.dates),
                "status": req.status,
                "reason": req.reason,
            }
        }
    except ValueError as e:
        return {"error": str(e), "code": "VALIDATION_ERROR"}
    except Exception as e:
        logger.exception("MCP tool error tool=create_wfh_request")
        return {"error": str(e), "code": "SERVER_ERROR"}


@tool("get_wfh_requests")
def get_wfh_requests(
    employee_id: int, requester_id: int, requester_role: str, input_data: dict | None = None
) -> dict:
    err = ensure_role(requester_role, ["employee", "manager", "hr", "admin"])
    if err:
        return err

    data = input_data or {}
    try:
        from apps.attendance.models import WFHRequest

        qs = WFHRequest.objects.select_related("employee__user").order_by("-created_at")

        if requester_role == "employee":
            qs = qs.filter(employee_id=employee_id)
        elif requester_role == "manager":
            from apps.employees.models import Employee
            manager = Employee.objects.filter(pk=requester_id).first()
            if manager:
                qs = qs.filter(employee__manager_id=manager.id)

        status_filter = data.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter.upper())

        items = []
        for req in qs[:30]:
            emp_name = req.employee.user.name if req.employee.user else req.employee.employee_id
            items.append({
                "id": req.pk,
                "employee_name": emp_name,
                "employee_id": req.employee.employee_id,
                "dates": req.dates,
                "dates_count": len(req.dates or []),
                "status": req.status,
                "reason": req.reason,
                "created_at": str(req.created_at),
            })

        logger.info("MCP tool ok tool=get_wfh_requests count=%s", len(items))
        return {"wfh_requests": items}
    except Exception as e:
        logger.exception("MCP tool error tool=get_wfh_requests")
        return {"error": str(e), "code": "SERVER_ERROR"}


@tool("approve_wfh_request")
def approve_wfh_request(
    employee_id: int, requester_id: int, requester_role: str, input_data: dict | None = None
) -> dict:
    err = ensure_role(requester_role, ["manager", "hr", "admin"])
    if err:
        return err

    data = input_data or {}
    wfh_id = data.get("wfh_id") or data.get("id")
    if not wfh_id:
        return {"error": "wfh_id is required", "code": "INVALID_INPUT"}

    try:
        from apps.attendance.models import WFHRequest
        from apps.attendance.services import WFHService
        from django.contrib.auth import get_user_model
        User = get_user_model()

        req = WFHRequest.objects.select_related("employee").filter(pk=wfh_id).first()
        if not req:
            return {"error": f"WFH request #{wfh_id} not found", "code": "NOT_FOUND"}

        approver = User.objects.filter(employee__id=requester_id).first()
        svc = WFHService(req.employee)
        req = svc.approve(req, approver)

        logger.info("MCP tool ok tool=approve_wfh_request id=%s", req.pk)
        return {"approved": True, "wfh_id": req.pk, "dates": req.dates, "status": req.status}
    except (ValueError, PermissionError) as e:
        return {"error": str(e), "code": "VALIDATION_ERROR"}
    except Exception as e:
        logger.exception("MCP tool error tool=approve_wfh_request")
        return {"error": str(e), "code": "SERVER_ERROR"}


@tool("reject_wfh_request")
def reject_wfh_request(
    employee_id: int, requester_id: int, requester_role: str, input_data: dict | None = None
) -> dict:
    err = ensure_role(requester_role, ["manager", "hr", "admin"])
    if err:
        return err

    data = input_data or {}
    wfh_id = data.get("wfh_id") or data.get("id")
    if not wfh_id:
        return {"error": "wfh_id is required", "code": "INVALID_INPUT"}

    try:
        from apps.attendance.models import WFHRequest
        from apps.attendance.services import WFHService
        from django.contrib.auth import get_user_model
        User = get_user_model()

        req = WFHRequest.objects.select_related("employee").filter(pk=wfh_id).first()
        if not req:
            return {"error": f"WFH request #{wfh_id} not found", "code": "NOT_FOUND"}

        approver = User.objects.filter(employee__id=requester_id).first()
        svc = WFHService(req.employee)
        req = svc.reject(req, approver, data.get("rejection_reason", ""))

        logger.info("MCP tool ok tool=reject_wfh_request id=%s", req.pk)
        return {"rejected": True, "wfh_id": req.pk, "status": req.status}
    except (ValueError, PermissionError) as e:
        return {"error": str(e), "code": "VALIDATION_ERROR"}
    except Exception as e:
        logger.exception("MCP tool error tool=reject_wfh_request")
        return {"error": str(e), "code": "SERVER_ERROR"}


# ── Penalties ─────────────────────────────────────────────────────────────────

@tool("get_attendance_penalties")
def get_attendance_penalties(
    employee_id: int, requester_id: int, requester_role: str, input_data: dict | None = None
) -> dict:
    err = ensure_role(requester_role, ["employee", "manager", "hr", "admin"])
    if err:
        return err

    data = input_data or {}
    try:
        from apps.attendance.models import AttendancePenalty

        qs = AttendancePenalty.objects.select_related("employee__user").order_by("-date")

        if requester_role == "employee":
            qs = qs.filter(employee_id=employee_id)
        elif requester_role == "manager":
            from apps.employees.models import Employee
            manager = Employee.objects.filter(pk=requester_id).first()
            if manager:
                qs = qs.filter(employee__manager_id=manager.id)

        status_filter = data.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter.upper())

        items = list(qs[:30].values(
            "id", "date", "penalty_type", "days_deducted", "status",
            "payroll_locked", "reversal_reason", "created_at",
        ))
        for item in items:
            item["date"] = str(item["date"])
            item["days_deducted"] = float(item["days_deducted"])

        logger.info("MCP tool ok tool=get_attendance_penalties count=%s", len(items))
        return {"attendance_penalties": items}
    except Exception as e:
        logger.exception("MCP tool error tool=get_attendance_penalties")
        return {"error": str(e), "code": "SERVER_ERROR"}


@tool("waive_attendance_penalty")
def waive_attendance_penalty(
    employee_id: int, requester_id: int, requester_role: str, input_data: dict | None = None
) -> dict:
    err = ensure_role(requester_role, ["hr", "admin"])
    if err:
        return err

    data = input_data or {}
    penalty_id = data.get("penalty_id") or data.get("id")
    if not penalty_id:
        return {"error": "penalty_id is required", "code": "INVALID_INPUT"}

    try:
        from apps.attendance.models import AttendancePenalty
        from apps.attendance.services import AttendancePenaltyService
        from django.contrib.auth import get_user_model
        User = get_user_model()

        penalty = AttendancePenalty.objects.select_related("employee").filter(pk=penalty_id).first()
        if not penalty:
            return {"error": f"Penalty #{penalty_id} not found", "code": "NOT_FOUND"}

        waiver = User.objects.filter(employee__id=requester_id).first()
        svc = AttendancePenaltyService()
        penalty = svc.waive(penalty, waiver, data.get("reason", ""))

        logger.info("MCP tool ok tool=waive_attendance_penalty id=%s", penalty.pk)
        return {"waived": True, "penalty_id": penalty.pk, "status": penalty.status}
    except (ValueError, PermissionError) as e:
        return {"error": str(e), "code": "VALIDATION_ERROR"}
    except Exception as e:
        logger.exception("MCP tool error tool=waive_attendance_penalty")
        return {"error": str(e), "code": "SERVER_ERROR"}
