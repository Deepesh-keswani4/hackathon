"""
Migration: attendance regularization, WFH, penalty audit, and attendance policy.
"""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("attendance", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ── 1. New statuses on AttendanceLog ──────────────────────────────────
        migrations.AlterField(
            model_name="attendancelog",
            name="status",
            field=models.CharField(
                max_length=20,
                choices=[
                    ("PRESENT", "Present"),
                    ("ABSENT", "Absent"),
                    ("WFH", "Work From Home"),
                    ("REGULARIZED", "Regularized"),
                    ("ON_LEAVE", "On Leave"),
                    ("WFH_PENDING", "WFH Pending Approval"),
                ],
                default="PRESENT",
            ),
        ),

        # ── 2. AttendancePolicy ───────────────────────────────────────────────
        migrations.CreateModel(
            name="AttendancePolicy",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("version", models.PositiveIntegerField(unique=True)),
                ("regularization_window_working_days", models.PositiveIntegerField(default=3)),
                ("wfh_min_lead_days", models.PositiveIntegerField(default=1)),
                ("penalty_order", models.JSONField(default=list)),
                ("is_active", models.BooleanField(default=True)),
                ("notes", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-version"]},
        ),

        # ── 3. RegularizationRequest (no FK to AttendanceLog yet) ────────────
        migrations.CreateModel(
            name="RegularizationRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("date", models.DateField()),
                ("requested_check_in", models.TimeField(blank=True, null=True)),
                ("requested_check_out", models.TimeField()),
                ("reason", models.TextField(blank=True, default="")),
                (
                    "status",
                    models.CharField(
                        max_length=20,
                        choices=[
                            ("PENDING", "Pending"),
                            ("APPROVED", "Approved"),
                            ("REJECTED", "Rejected"),
                            ("CANCELLED", "Cancelled"),
                        ],
                        default="PENDING",
                    ),
                ),
                ("rejection_reason", models.TextField(blank=True, default="")),
                ("attempt_number", models.PositiveSmallIntegerField(default=1)),
                ("penalty_reversed", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "employee",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="regularization_requests",
                        to="employees.employee",
                    ),
                ),
                (
                    "applied_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="regularizations_applied",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "reviewed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="regularizations_reviewed",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "attendance_log",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="regularization_requests",
                        to="attendance.attendancelog",
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="regularizationrequest",
            index=models.Index(fields=["employee", "date", "status"], name="reg_emp_date_status_idx"),
        ),

        # ── 4. WFHRequest ─────────────────────────────────────────────────────
        migrations.CreateModel(
            name="WFHRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("dates", models.JSONField()),
                ("reason", models.TextField(blank=True, default="")),
                (
                    "status",
                    models.CharField(
                        max_length=20,
                        choices=[
                            ("PENDING", "Pending"),
                            ("APPROVED", "Approved"),
                            ("REJECTED", "Rejected"),
                            ("CANCELLED", "Cancelled"),
                        ],
                        default="PENDING",
                    ),
                ),
                ("rejection_reason", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "employee",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="wfh_requests",
                        to="employees.employee",
                    ),
                ),
                (
                    "applied_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="wfh_applied",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "reviewed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="wfh_reviewed",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),

        # ── 5. AttendancePenalty ──────────────────────────────────────────────
        migrations.CreateModel(
            name="AttendancePenalty",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("date", models.DateField()),
                (
                    "penalty_type",
                    models.CharField(
                        max_length=3,
                        choices=[("PL", "Privilege Leave"), ("LOP", "Loss of Pay")],
                    ),
                ),
                ("days_deducted", models.DecimalField(max_digits=4, decimal_places=2)),
                (
                    "status",
                    models.CharField(
                        max_length=20,
                        choices=[
                            ("ACTIVE", "Active"),
                            ("REVERSED", "Reversed"),
                            ("WAIVED", "Waived"),
                        ],
                        default="ACTIVE",
                    ),
                ),
                ("reversal_reason", models.TextField(blank=True, default="")),
                ("reversed_at", models.DateTimeField(blank=True, null=True)),
                ("payroll_locked", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "employee",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attendance_penalties",
                        to="employees.employee",
                    ),
                ),
                (
                    "reversed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="penalties_reversed",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "regularization_request",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="penalties",
                        to="attendance.regularizationrequest",
                    ),
                ),
            ],
            options={"ordering": ["-date", "-created_at"]},
        ),
        migrations.AddIndex(
            model_name="attendancepenalty",
            index=models.Index(fields=["employee", "date", "status"], name="penalty_emp_date_status_idx"),
        ),

        # ── 6. AttendanceLog FK to RegularizationRequest ─────────────────────
        migrations.AddField(
            model_name="attendancelog",
            name="regularization_request",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="attendance_logs",
                to="attendance.regularizationrequest",
            ),
        ),
    ]
