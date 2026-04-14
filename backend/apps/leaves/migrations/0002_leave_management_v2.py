import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("leaves", "0001_initial"),
        ("employees", "0002_alter_user_options_alter_user_managers_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ── LeavePolicy: expand leave_type + add new columns ──────────────────
        migrations.AlterField(
            model_name="leavepolicy",
            name="leave_type",
            field=models.CharField(
                choices=[
                    ("CL", "Casual Leave"),
                    ("PL", "Privilege Leave"),
                    ("SL", "Sick Leave"),
                    ("CO", "Comp Off"),
                    ("LOP", "Loss of Pay"),
                ],
                max_length=3,
                unique=True,
            ),
        ),
        migrations.AddField(
            model_name="leavepolicy",
            name="requires_balance",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="leavepolicy",
            name="allow_backdate_days",
            field=models.IntegerField(default=0),
        ),

        # ── LeaveBalance: rename earned→privilege, add comp_off ──────────────
        migrations.RenameField(
            model_name="leavebalance",
            old_name="earned_remaining",
            new_name="privilege_remaining",
        ),
        migrations.AddField(
            model_name="leavebalance",
            name="comp_off_remaining",
            field=models.FloatField(default=0),
        ),

        # ── LeaveRequest: expand leave_type, add new fields ──────────────────
        migrations.AlterField(
            model_name="leaverequest",
            name="leave_type",
            field=models.CharField(
                choices=[
                    ("CL", "Casual Leave"),
                    ("PL", "Privilege Leave"),
                    ("SL", "Sick Leave"),
                    ("CO", "Comp Off"),
                    ("LOP", "Loss of Pay"),
                ],
                max_length=3,
            ),
        ),
        migrations.AlterField(
            model_name="leaverequest",
            name="status",
            field=models.CharField(
                choices=[
                    ("PENDING", "Pending"),
                    ("APPROVED", "Approved"),
                    ("REJECTED", "Rejected"),
                    ("CANCELLED", "Cancelled"),
                ],
                default="PENDING",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="leaverequest",
            name="reason",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="leaverequest",
            name="rejection_reason",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="leaverequest",
            name="is_half_day",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="leaverequest",
            name="half_day_session",
            field=models.CharField(
                blank=True,
                choices=[("AM", "First Half"), ("PM", "Second Half")],
                default="",
                max_length=2,
            ),
        ),
        migrations.AddField(
            model_name="leaverequest",
            name="applied_by",
            field=models.ForeignKey(
                blank=True,
                help_text="Who applied this leave — employee themselves or manager on behalf",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="leaves_applied_by_me",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="leaverequest",
            name="balance_deducted",
            field=models.BooleanField(default=False),
        ),

        # ── CompOffRequest: new model ─────────────────────────────────────────
        migrations.CreateModel(
            name="CompOffRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("worked_on", models.DateField(help_text="Date the employee worked (holiday/weekend)")),
                ("days_claimed", models.FloatField(default=1.0)),
                ("reason", models.TextField(blank=True, default="")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pending"),
                            ("APPROVED", "Approved"),
                            ("REJECTED", "Rejected"),
                        ],
                        default="PENDING",
                        max_length=20,
                    ),
                ),
                ("rejection_reason", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "employee",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="comp_off_requests",
                        to="employees.employee",
                    ),
                ),
                (
                    "approved_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="approved_comp_offs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
