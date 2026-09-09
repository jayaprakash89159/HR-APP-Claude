from django.contrib import admin

from .models import EmployeeSalary, LoanRecord, PayrollPeriod, PayslipRecord, SalaryComponent, SalaryStructure, SalaryStructureComponent


@admin.register(SalaryComponent)
class SalaryComponentAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'component_type', 'calculation_type', 'is_statutory', 'is_active')
    list_filter = ('component_type', 'calculation_type', 'is_statutory', 'is_active')
    search_fields = ('code', 'name')


class SalaryStructureComponentInline(admin.TabularInline):
    model = SalaryStructureComponent
    extra = 1
    autocomplete_fields = ('component',)


@admin.register(SalaryStructure)
class SalaryStructureAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('code', 'name')
    inlines = (SalaryStructureComponentInline,)


@admin.register(EmployeeSalary)
class EmployeeSalaryAdmin(admin.ModelAdmin):
    list_display = ('employee', 'salary_structure', 'monthly_ctc', 'effective_from', 'effective_to', 'is_active')
    list_filter = ('salary_type', 'is_active', 'salary_structure')
    search_fields = ('employee__employee_code', 'employee__first_name', 'employee__last_name')
    autocomplete_fields = ('employee', 'salary_structure', 'revised_by')


@admin.register(PayrollPeriod)
class PayrollPeriodAdmin(admin.ModelAdmin):
    list_display = ('name', 'month', 'year', 'status', 'total_employees', 'total_net')
    list_filter = ('status', 'year')
    search_fields = ('name',)


@admin.register(PayslipRecord)
class PayslipRecordAdmin(admin.ModelAdmin):
    list_display = ('payslip_number', 'employee', 'payroll_period', 'net_salary', 'status', 'payment_date')
    list_filter = ('status', 'payment_date')
    search_fields = ('payslip_number', 'employee__employee_code', 'employee__first_name', 'employee__last_name')
    readonly_fields = ('payslip_number', 'created_at', 'updated_at')


@admin.register(LoanRecord)
class LoanRecordAdmin(admin.ModelAdmin):
    list_display = ('employee', 'loan_type', 'loan_amount', 'outstanding_amount', 'status')
    list_filter = ('loan_type', 'status')
    search_fields = ('employee__employee_code', 'employee__first_name', 'employee__last_name')