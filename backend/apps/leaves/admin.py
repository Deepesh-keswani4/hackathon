from django.contrib import admin

from .models import CompOffRequest, LeaveBalance, LeavePolicy, LeaveRequest


@admin.register(LeavePolicy)
class LeavePolicyAdmin(admin.ModelAdmin):
    list_display = ("leave_type", "annual_allocation", "accrual_per_month", "requires_balance", "allow_backdate_days", "created_at")


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ("employee", "casual_remaining", "privilege_remaining", "sick_remaining", "comp_off_remaining", "updated_at")


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "employee", "leave_type", "from_date", "to_date", "days_count", "is_half_day", "status", "spof_flag", "conflict_flag", "created_at")
    list_filter = ("status", "leave_type", "is_half_day")
    search_fields = ("employee__employee_id", "employee__user__name")


@admin.register(CompOffRequest)
class CompOffRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "employee", "worked_on", "days_claimed", "status", "approved_by", "created_at")
    list_filter = ("status",)
    search_fields = ("employee__employee_id", "employee__user__name")
