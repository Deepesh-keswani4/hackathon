import logging
from datetime import date, timedelta

from config.celery import app
from core.tasks.base import BaseHRMSTask

logger = logging.getLogger("hrms")


def _working_days_ago(n: int, from_date: date | None = None) -> date:
    """Return date that is n working days before from_date (default: today)."""
    current = from_date or date.today()
    count = 0
    while count < n:
        current -= timedelta(days=1)
        if current.weekday() < 5:
            count += 1
    return current


class CreateDailyAttendanceLogsTask(BaseHRMSTask):
    """
    Beat: runs at midnight (00:05) each day.
    Creates AttendanceLog(status=ABSENT) for all active employees who have no log for today.
    Also marks payroll_locked=True on penalties from the previous month on last working day.
    """
    name = "tasks.attendance_tasks.create_daily_attendance_logs"

    def execute(self):
        from apps.attendance.models import AttendanceLog, AttendancePenalty
        from apps.employees.models import Employee

        today = date.today()
        employees = Employee.objects.filter(is_active=True).values_list("id", flat=True)
        created = 0

        # Check if we need to check approved leaves covering today
        from apps.leaves.models import LeaveRequest

        for emp_id in employees:
            try:
                existing = AttendanceLog.objects.filter(employee_id=emp_id, date=today).first()
                if existing:
                    continue

                # Check approved leave covering today → ON_LEAVE
                on_leave = LeaveRequest.objects.filter(
                    employee_id=emp_id,
                    status=LeaveRequest.STATUS_APPROVED,
                    from_date__lte=today,
                    to_date__gte=today,
                ).exists()

                status = AttendanceLog.STATUS_ON_LEAVE if on_leave else AttendanceLog.STATUS_ABSENT
                AttendanceLog.objects.get_or_create(
                    employee_id=emp_id,
                    date=today,
                    defaults={"status": status},
                )
                created += 1
            except Exception:
                logger.exception("create_daily_attendance_logs failed employee_id=%s date=%s", emp_id, today)

        # Lock penalties from previous month on last working day of month
        _lock_previous_month_penalties(today)

        logger.info("Daily attendance logs created count=%s date=%s", created, today)
        return {"status": "ok", "created": created, "date": str(today)}


def _lock_previous_month_penalties(today: date):
    """Flip payroll_locked=True for all previous-month ACTIVE penalties on last working day."""
    from apps.attendance.models import AttendancePenalty

    # Is today the last working day of the month?
    if today.month == 12:
        next_month = date(today.year + 1, 1, 1)
    else:
        next_month = date(today.year, today.month + 1, 1)
    last_day = next_month - timedelta(days=1)
    while last_day.weekday() >= 5:
        last_day -= timedelta(days=1)

    if today != last_day:
        return

    prev_month = today.month - 1 if today.month > 1 else 12
    prev_year = today.year if today.month > 1 else today.year - 1

    updated = AttendancePenalty.objects.filter(
        date__year=prev_year,
        date__month=prev_month,
        payroll_locked=False,
    ).update(payroll_locked=True)
    logger.info("Payroll lock applied penalties=%s month=%s/%s", updated, prev_month, prev_year)


class ScanAttendanceAnomaliesTask(BaseHRMSTask):
    """
    Beat: runs daily at 01:00.
    Finds employees with overdue unregularized anomalies → applies penalty.
    Idempotent: skips if penalty already exists for that date.
    """
    name = "tasks.attendance_tasks.scan_attendance_anomalies"

    def execute(self):
        from apps.attendance.models import AttendanceLog, AttendancePenalty, RegularizationRequest, WFHRequest
        from apps.attendance.services import AttendancePenaltyService, AttendancePolicyService
        from apps.employees.models import Employee

        policy_svc = AttendancePolicyService()
        policy = policy_svc.get_active_or_default()
        window = policy["regularization_window_working_days"]
        penalty_svc = AttendancePenaltyService(policy_service=policy_svc)

        today = date.today()
        deadline = _working_days_ago(window, today)  # anomalies on or before this date are overdue

        # Find all ABSENT logs (no check_in or no check_out) on or before deadline
        anomaly_logs = AttendanceLog.objects.filter(
            date__lte=deadline,
            status=AttendanceLog.STATUS_ABSENT,
        ).select_related("employee")

        penalized = 0
        skipped = 0

        for log in anomaly_logs:
            try:
                emp = log.employee
                if not emp.is_active:
                    continue

                # Skip if PENDING or APPROVED regularization exists
                reg_freeze = RegularizationRequest.objects.filter(
                    employee_id=emp.id,
                    date=log.date,
                    status__in=[RegularizationRequest.STATUS_PENDING, RegularizationRequest.STATUS_APPROVED],
                ).exists()
                if reg_freeze:
                    skipped += 1
                    continue

                # Skip if PENDING or APPROVED WFH covers this date
                wfh_freeze = WFHRequest.objects.filter(
                    employee_id=emp.id,
                    status__in=[WFHRequest.STATUS_PENDING, WFHRequest.STATUS_APPROVED],
                    dates__contains=log.date.isoformat(),
                ).exists()
                if wfh_freeze:
                    skipped += 1
                    continue

                # Skip if penalty already applied (idempotency)
                already = AttendancePenalty.objects.filter(
                    employee_id=emp.id,
                    date=log.date,
                    status=AttendancePenalty.STATUS_ACTIVE,
                ).exists()
                if already:
                    skipped += 1
                    continue

                penalties = penalty_svc.apply_penalty(emp, log.date)
                if penalties:
                    penalized += 1
                    _notify_penalty_applied.delay(emp.id, str(log.date))

            except Exception:
                logger.exception("Anomaly scan failed employee_id=%s date=%s", log.employee_id, log.date)

        logger.info("Anomaly scan complete penalized=%s skipped=%s deadline=%s", penalized, skipped, deadline)
        return {"status": "ok", "penalized": penalized, "skipped": skipped}


class NotifyPrePayrollPenaltiesTask(BaseHRMSTask):
    """
    Beat: runs on 25th of each month at 09:00.
    Sends HR a summary of employees with active LOP/PL penalties for current month.
    """
    name = "tasks.attendance_tasks.notify_prepayroll_penalties"

    def execute(self):
        from apps.attendance.models import AttendancePenalty
        from apps.employees.models import Employee

        today = date.today()
        penalties = (
            AttendancePenalty.objects
            .filter(date__year=today.year, date__month=today.month, status=AttendancePenalty.STATUS_ACTIVE)
            .select_related("employee__user", "employee__manager__user")
        )
        if not penalties.exists():
            return {"status": "ok", "count": 0}

        # Get HR emails
        hr_employees = Employee.objects.filter(role__in=["hr", "admin"], is_active=True).select_related("user")
        hr_emails = [e.user.email for e in hr_employees if e.user and e.user.email]
        if not hr_emails:
            logger.warning("No HR emails found for prepayroll penalty notification")
            return {"status": "ok", "count": penalties.count(), "notified": 0}

        from tasks.notification_tasks import dispatch_notification

        summary_lines = []
        for p in penalties[:50]:
            emp_name = p.employee.user.name if p.employee.user else p.employee.employee_id
            summary_lines.append(f"• {emp_name} — {p.date} — {p.penalty_type} {p.days_deducted}d")

        body = (
            f"Pre-payroll alert: {penalties.count()} active attendance penalty/penalties for "
            f"{today.strftime('%B %Y')} not yet resolved.\n\n" + "\n".join(summary_lines)
        )

        for email in hr_emails:
            try:
                dispatch_notification.delay(
                    ["inapp"],
                    email,
                    f"[Action Required] Attendance Penalties — {today.strftime('%B %Y')}",
                    body,
                    {"type": "prepayroll_penalty_alert", "month": today.month, "year": today.year},
                )
            except Exception:
                logger.exception("Pre-payroll notify failed for hr_email=%s", email)

        return {"status": "ok", "count": penalties.count(), "notified": len(hr_emails)}


class DispatchRegularizationNotificationTask(BaseHRMSTask):
    name = "tasks.attendance_tasks.dispatch_regularization_notification"

    def execute(self, reg_id: int):
        from apps.attendance.models import RegularizationRequest

        req = (
            RegularizationRequest.objects
            .select_related("employee__user", "employee__manager__user", "reviewed_by__user")
            .filter(pk=reg_id)
            .first()
        )
        if not req:
            return {"status": "not_found"}

        from tasks.notification_tasks import dispatch_notification

        emp_name = req.employee.user.name if req.employee.user else req.employee.employee_id
        manager = req.employee.manager
        manager_email = manager.user.email if manager and hasattr(manager, "user") and manager.user else ""

        if req.status == RegularizationRequest.STATUS_PENDING and manager_email:
            dispatch_notification.delay(
                ["inapp"],
                manager_email,
                f"Regularization Request — {emp_name} ({req.date})",
                (
                    f"{emp_name} has submitted a regularization request for {req.date}. "
                    f"Check-out: {req.requested_check_out}. Reason: {req.reason or 'Not provided'}."
                ),
                {
                    "regularization_id": req.pk,
                    "employee_id": req.employee.employee_id,
                    "date": str(req.date),
                    "status": req.status,
                },
            )
        elif req.status in (RegularizationRequest.STATUS_APPROVED, RegularizationRequest.STATUS_REJECTED):
            emp_email = req.employee.user.email if req.employee.user else ""
            actioned_by_name = req.reviewed_by.name if req.reviewed_by and hasattr(req.reviewed_by, "name") else None
            if emp_email:
                dispatch_notification.delay(
                    ["inapp"],
                    emp_email,
                    f"Regularization #{req.pk} {req.status.title()} — {req.date}",
                    (
                        f"Your regularization request for {req.date} has been {req.status.lower()}."
                        + (f" Reason: {req.rejection_reason}" if req.rejection_reason else "")
                        + (" Your attendance penalty has been reversed." if req.penalty_reversed else "")
                    ),
                    {
                        "regularization_id": req.pk,
                        "date": str(req.date),
                        "status": req.status,
                        "penalty_reversed": req.penalty_reversed,
                        "actioned_by_name": actioned_by_name,
                    },
                )

        return {"status": "ok"}


class DispatchWFHNotificationTask(BaseHRMSTask):
    name = "tasks.attendance_tasks.dispatch_wfh_notification"

    def execute(self, wfh_id: int):
        from apps.attendance.models import WFHRequest

        req = (
            WFHRequest.objects
            .select_related("employee__user", "employee__manager__user", "reviewed_by")
            .filter(pk=wfh_id)
            .first()
        )
        if not req:
            return {"status": "not_found"}

        from tasks.notification_tasks import dispatch_notification

        emp_name = req.employee.user.name if req.employee.user else req.employee.employee_id
        manager = req.employee.manager
        manager_email = manager.user.email if manager and hasattr(manager, "user") and manager.user else ""
        emp_email = req.employee.user.email if req.employee.user else ""
        dates_str = ", ".join(req.dates[:5]) + (f" (+{len(req.dates)-5} more)" if len(req.dates) > 5 else "")

        if req.status == WFHRequest.STATUS_PENDING and manager_email:
            dispatch_notification.delay(
                ["inapp"],
                manager_email,
                f"WFH Request — {emp_name}",
                f"{emp_name} has requested WFH for: {dates_str}. Reason: {req.reason or 'Not provided'}.",
                {
                    "wfh_id": req.pk,
                    "employee_id": req.employee.employee_id,
                    "dates": req.dates,
                    "status": req.status,
                },
            )
        elif req.status in (WFHRequest.STATUS_APPROVED, WFHRequest.STATUS_REJECTED) and emp_email:
            actioned_by_name = req.reviewed_by.name if req.reviewed_by and hasattr(req.reviewed_by, "name") else None
            dispatch_notification.delay(
                ["inapp"],
                emp_email,
                f"WFH Request #{req.pk} {req.status.title()}",
                (
                    f"Your WFH request for {dates_str} has been {req.status.lower()}."
                    + (f" Reason: {req.rejection_reason}" if req.rejection_reason else "")
                ),
                {
                    "wfh_id": req.pk,
                    "dates": req.dates,
                    "status": req.status,
                    "actioned_by_name": actioned_by_name,
                },
            )

        return {"status": "ok"}


@app.task(name="tasks.attendance_tasks._notify_penalty_applied", bind=True, max_retries=2)
def _notify_penalty_applied(self, employee_id: int, date_str: str):
    """Notify employee + manager when penalty is applied."""
    try:
        from apps.employees.models import Employee
        from tasks.notification_tasks import dispatch_notification

        emp = Employee.objects.select_related("user", "manager__user").filter(pk=employee_id).first()
        if not emp:
            return
        emp_email = emp.user.email if emp.user else ""
        manager_email = emp.manager.user.email if emp.manager and emp.manager.user else ""

        msg = (
            f"Attendance penalty applied for {date_str}. "
            "No regularization was submitted within the allowed window. "
            "Contact your manager to reverse this if you believe it's incorrect."
        )
        meta = {"type": "attendance_penalty", "date": date_str, "employee_id": emp.employee_id}

        if emp_email:
            dispatch_notification.delay(["inapp"], emp_email, f"Attendance Penalty — {date_str}", msg, meta)
        if manager_email:
            emp_name = emp.user.name if emp.user else emp.employee_id
            dispatch_notification.delay(
                ["inapp"], manager_email,
                f"Attendance Penalty Applied — {emp_name} ({date_str})",
                f"A penalty was automatically applied for {emp_name} for date {date_str}. "
                "You can submit a regularization on their behalf.",
                {**meta, "employee_name": emp_name},
            )
    except Exception:
        logger.exception("_notify_penalty_applied failed employee_id=%s date=%s", employee_id, date_str)


# Register tasks
create_daily_attendance_logs = app.register_task(CreateDailyAttendanceLogsTask())
scan_attendance_anomalies = app.register_task(ScanAttendanceAnomaliesTask())
notify_prepayroll_penalties = app.register_task(NotifyPrePayrollPenaltiesTask())
dispatch_regularization_notification = app.register_task(DispatchRegularizationNotificationTask())
dispatch_wfh_notification = app.register_task(DispatchWFHNotificationTask())
