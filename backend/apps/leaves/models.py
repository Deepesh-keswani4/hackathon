from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class LeavePolicy(models.Model):
    TYPE_CL = "CL"

    TYPE_PL = "PL"
    TYPE_SL = "SL"
    TYPE_CO = "CO"  # Comp Off — granted by manager; no accrual
    TYPE_LOP = "LOP"  # Loss of Pay — no balance; always available

    TYPE_CHOICES = (
        (TYPE_CL, "Casual Leave"),
        (TYPE_PL, "Privilege Leave"),
        (TYPE_SL, "Sick Leave"),
        (TYPE_CO, "Comp Off"),
        (TYPE_LOP, "Loss of Pay"),
    )

    leave_type = models.CharField(max_length=3, choices=TYPE_CHOICES, unique=True)
    annual_allocation = models.FloatField(default=0)
    accrual_per_month = models.FloatField(default=0)
    # CO and LOP are exempt from balance checks
    requires_balance = models.BooleanField(default=True)
    allow_backdate_days = models.IntegerField(default=0)  # SL allows backdating
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["leave_type"]

    def __str__(self) -> str:
        return f"{self.leave_type} policy"


class LeaveBalance(models.Model):
    employee = models.OneToOneField("employees.Employee", on_delete=models.CASCADE, related_name="leave_balance")
    casual_remaining = models.FloatField(default=0)
    privilege_remaining = models.FloatField(default=0)
    sick_remaining = models.FloatField(default=0)
    comp_off_remaining = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["employee__employee_id"]

    def __str__(self) -> str:
        return f"LeaveBalance {self.employee.employee_id}"

    def get_remaining(self, leave_type: str) -> float:
        field = {
            "CL": "casual_remaining",
            "PL": "privilege_remaining",
            "SL": "sick_remaining",
            "CO": "comp_off_remaining",
        }.get(leave_type)
        if not field:
            return 0.0
        return float(getattr(self, field, 0))

    def deduct(self, leave_type: str, days: float) -> None:
        field = {
            "CL": "casual_remaining",
            "PL": "privilege_remaining",
            "SL": "sick_remaining",
            "CO": "comp_off_remaining",
        }.get(leave_type)
        if not field:
            return
        current = float(getattr(self, field, 0))
        setattr(self, field, max(0.0, current - days))
        self.save(update_fields=[field, "updated_at"])

    def credit(self, leave_type: str, days: float) -> None:
        """Credit back on cancellation or rejection after approval."""
        field = {
            "CL": "casual_remaining",
            "PL": "privilege_remaining",
            "SL": "sick_remaining",
            "CO": "comp_off_remaining",
        }.get(leave_type)
        if not field:
            return
        current = float(getattr(self, field, 0))
        setattr(self, field, current + days)
        self.save(update_fields=[field, "updated_at"])


class CompOffRequest(models.Model):
    """
    Employee worked on a holiday/weekend → requests comp-off credit.
    Manager approves → CO balance is credited.
    """

    STATUS_PENDING = "PENDING"
    STATUS_APPROVED = "APPROVED"
    STATUS_REJECTED = "REJECTED"
    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    )

    employee = models.ForeignKey(
        "employees.Employee", on_delete=models.CASCADE, related_name="comp_off_requests"
    )
    worked_on = models.DateField(help_text="Date the employee worked (holiday/weekend)")
    days_claimed = models.FloatField(default=1.0)
    reason = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_comp_offs",
    )
    rejection_reason = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"CompOff {self.pk} {self.employee.employee_id} {self.worked_on} {self.status}"


class LeaveRequest(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_APPROVED = "APPROVED"
    STATUS_REJECTED = "REJECTED"
    STATUS_CANCELLED = "CANCELLED"

    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_CANCELLED, "Cancelled"),
    )

    HALF_DAY_AM = "AM"
    HALF_DAY_PM = "PM"
    HALF_DAY_CHOICES = (
        (HALF_DAY_AM, "First Half"),
        (HALF_DAY_PM, "Second Half"),
    )

    employee = models.ForeignKey("employees.Employee", on_delete=models.CASCADE, related_name="leave_requests")
    applied_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leaves_applied_by_me",
        help_text="Who applied this leave — employee themselves or manager on behalf",
    )
    approver = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_leaves",
    )

    leave_type = models.CharField(max_length=3, choices=LeavePolicy.TYPE_CHOICES)
    from_date = models.DateField()
    to_date = models.DateField()
    days_count = models.FloatField(default=0)
    reason = models.TextField(blank=True, default="")

    is_half_day = models.BooleanField(default=False)
    half_day_session = models.CharField(
        max_length=2, choices=HALF_DAY_CHOICES, blank=True, default=""
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    rejection_reason = models.TextField(blank=True, default="")

    spof_flag = models.BooleanField(default=False)
    conflict_flag = models.BooleanField(default=False)
    conflict_context = models.JSONField(default=dict, blank=True)
    ai_context_card = models.TextField(blank=True, default="")

    # Track if balance was already deducted (on approval) to prevent double-deduction
    balance_deducted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"LeaveRequest {self.pk} {self.employee.employee_id} {self.leave_type} {self.status}"
