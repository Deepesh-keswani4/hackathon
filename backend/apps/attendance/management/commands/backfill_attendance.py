"""
Backfill AttendanceLog for all active employees for the past N weeks.
Each working day (Mon-Fri) gets a random status: PRESENT (70%), WFH (20%), ABSENT (10%).

Usage:
    python manage.py backfill_attendance
    python manage.py backfill_attendance --weeks 6
    python manage.py backfill_attendance --weeks 4 --clear
"""
import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.attendance.models import AttendanceLog
from apps.employees.models import Employee


class Command(BaseCommand):
    help = "Backfill random attendance logs for all employees for past N weeks"

    def add_arguments(self, parser):
        parser.add_argument("--weeks", type=int, default=4, help="How many weeks to backfill (default: 4)")
        parser.add_argument("--clear", action="store_true", help="Delete existing logs in range before inserting")

    def handle(self, *args, **options):
        weeks = options["weeks"]
        clear = options["clear"]

        today = date.today()
        start = today - timedelta(weeks=weeks)

        employees = list(Employee.objects.filter(is_active=True).values_list("id", flat=True))
        if not employees:
            self.stdout.write(self.style.WARNING("No active employees found."))
            return

        # Collect all working days (Mon–Fri) in range
        working_days = []
        d = start
        while d <= today:
            if d.weekday() < 5:  # Mon=0 … Fri=4
                working_days.append(d)
            d += timedelta(days=1)

        if clear:
            deleted, _ = AttendanceLog.objects.filter(
                date__gte=start, date__lte=today
            ).delete()
            self.stdout.write(f"Cleared {deleted} existing logs.")

        # Per-employee random distribution: PRESENT 65%, WFH 22%, ABSENT 13%
        STATUSES = (
            [AttendanceLog.STATUS_PRESENT] * 65
            + [AttendanceLog.STATUS_WFH] * 22
            + [AttendanceLog.STATUS_ABSENT] * 13
        )

        to_create = []
        existing = set(
            AttendanceLog.objects.filter(date__gte=start, date__lte=today)
            .values_list("employee_id", "date")
        )

        for emp_id in employees:
            for day in working_days:
                if (emp_id, day) in existing:
                    continue
                status = random.choice(STATUSES)
                to_create.append(
                    AttendanceLog(
                        employee_id=emp_id,
                        date=day,
                        status=status,
                    )
                )

        with transaction.atomic():
            AttendanceLog.objects.bulk_create(to_create, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS(
            f"Created {len(to_create)} attendance logs for {len(employees)} employees "
            f"across {len(working_days)} working days ({weeks} weeks)."
        ))
