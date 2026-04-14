from rest_framework import serializers

from .models import CompOffRequest, LeaveBalance, LeavePolicy, LeaveRequest


class LeaveRequestSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    leave_type_display = serializers.SerializerMethodField()
    applied_by_name = serializers.SerializerMethodField()

    class Meta:
        model = LeaveRequest
        fields = (
            "id",
            "employee",
            "employee_name",
            "applied_by",
            "applied_by_name",
            "approver",
            "leave_type",
            "leave_type_display",
            "from_date",
            "to_date",
            "days_count",
            "reason",
            "is_half_day",
            "half_day_session",
            "status",
            "rejection_reason",
            "spof_flag",
            "conflict_flag",
            "conflict_context",
            "ai_context_card",
            "balance_deducted",
            "created_at",
        )

    def get_employee_name(self, obj):
        return obj.employee.user.name if obj.employee and obj.employee.user else None

    def get_leave_type_display(self, obj):
        return obj.get_leave_type_display()

    def get_applied_by_name(self, obj):
        return obj.applied_by.get_full_name() if obj.applied_by else None


class LeaveApplySerializer(serializers.Serializer):
    LEAVE_TYPE_CHOICES = LeaveRequest._meta.get_field("leave_type").choices

    leave_type = serializers.ChoiceField(choices=LEAVE_TYPE_CHOICES)
    from_date = serializers.DateField()
    to_date = serializers.DateField()
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")
    is_half_day = serializers.BooleanField(required=False, default=False)
    half_day_session = serializers.ChoiceField(
        choices=LeaveRequest.HALF_DAY_CHOICES, required=False, allow_blank=True, default=""
    )

    def validate(self, data):
        if data.get("is_half_day") and not data.get("half_day_session"):
            raise serializers.ValidationError("half_day_session (AM/PM) is required for half-day leave")
        return data


class LeaveRejectSerializer(serializers.Serializer):
    rejection_reason = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")


class LeaveSimulateSerializer(serializers.Serializer):
    LEAVE_TYPE_CHOICES = LeaveRequest._meta.get_field("leave_type").choices

    leave_type = serializers.ChoiceField(choices=LEAVE_TYPE_CHOICES)
    days = serializers.IntegerField(min_value=1)


class LeaveBalanceSerializer(serializers.ModelSerializer):
    summaries = serializers.SerializerMethodField()

    class Meta:
        model = LeaveBalance
        fields = ("casual_remaining", "privilege_remaining", "sick_remaining", "comp_off_remaining", "summaries", "updated_at")

    def get_summaries(self, obj):
        return [
            {"type": "CL", "label": "Casual Leave", "remaining": obj.casual_remaining},
            {"type": "PL", "label": "Privilege Leave", "remaining": obj.privilege_remaining},
            {"type": "SL", "label": "Sick Leave", "remaining": obj.sick_remaining},
            {"type": "CO", "label": "Comp Off", "remaining": obj.comp_off_remaining},
            {"type": "LOP", "label": "Loss of Pay", "remaining": None, "note": "Always available, deducted from salary"},
        ]


class LeavePolicySerializer(serializers.ModelSerializer):
    leave_type_display = serializers.SerializerMethodField()

    class Meta:
        model = LeavePolicy
        fields = (
            "leave_type",
            "leave_type_display",
            "annual_allocation",
            "accrual_per_month",
            "requires_balance",
            "allow_backdate_days",
        )

    def get_leave_type_display(self, obj):
        return obj.get_leave_type_display()


class CompOffRequestSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    approved_by_name = serializers.SerializerMethodField()

    class Meta:
        model = CompOffRequest
        fields = (
            "id",
            "employee",
            "employee_name",
            "worked_on",
            "days_claimed",
            "reason",
            "status",
            "rejection_reason",
            "approved_by",
            "approved_by_name",
            "created_at",
        )

    def get_employee_name(self, obj):
        return obj.employee.user.name if obj.employee and obj.employee.user else None

    def get_approved_by_name(self, obj):
        return obj.approved_by.get_full_name() if obj.approved_by else None


class CompOffRequestCreateSerializer(serializers.Serializer):
    worked_on = serializers.DateField()
    days_claimed = serializers.FloatField(min_value=0.5, max_value=2.0, default=1.0)
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")


class CompOffRejectSerializer(serializers.Serializer):
    rejection_reason = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")
