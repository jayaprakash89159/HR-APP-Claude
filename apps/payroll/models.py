"""
WorkSphere HR - Payroll Models
Complete payroll processing with Indian compliance
"""
from django.db import models
from django.conf import settings
from apps.employees.models import Employee
import uuid


class SalaryStructure(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'hr_salary_structures'

    def __str__(self):
        return self.name


class SalaryStructureComponent(models.Model):
    """A component included in a salary structure, in display/calculation order."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    salary_structure = models.ForeignKey(
        SalaryStructure, on_delete=models.CASCADE, related_name='components'
    )
    component = models.ForeignKey(
        'SalaryComponent', on_delete=models.PROTECT, related_name='structures'
    )
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'hr_salary_structure_components'
        ordering = ['display_order', 'component__display_order', 'component__name']
        constraints = [
            models.UniqueConstraint(
                fields=['salary_structure', 'component'],
                name='unique_salary_structure_component',
            ),
        ]

    def __str__(self):
        return f'{self.salary_structure} - {self.component}'


class SalaryComponent(models.Model):
    COMPONENT_TYPE_CHOICES = [('earning', 'Earning'), ('deduction', 'Deduction')]
    CALCULATION_TYPE_CHOICES = [
        ('fixed', 'Fixed Amount'),
        ('percentage', 'Percentage of Basic'),
        ('percentage_ctc', 'Percentage of CTC'),
        ('formula', 'Formula Based'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    component_type = models.CharField(max_length=10, choices=COMPONENT_TYPE_CHOICES)
    calculation_type = models.CharField(max_length=20, choices=CALCULATION_TYPE_CHOICES, default='fixed')
    fixed_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    percentage = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    formula = models.TextField(blank=True)
    is_taxable = models.BooleanField(default=True)
    is_statutory = models.BooleanField(default=False)
    is_pf_applicable = models.BooleanField(default=False)
    is_esi_applicable = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    # Common Indian salary components
    COMMON_COMPONENTS = {
        'BASIC': 'Basic Salary',
        'HRA': 'House Rent Allowance',
        'SPEC': 'Special Allowance',
        'MED': 'Medical Allowance',
        'CONV': 'Conveyance Allowance',
        'BONUS': 'Bonus',
        'PERF': 'Performance Incentive',
        'OT': 'Overtime',
        'ARR': 'Arrears',
        'PF': 'Provident Fund',
        'ESI': 'ESI',
        'PT': 'Professional Tax',
        'TDS': 'TDS',
        'LWF': 'Labour Welfare Fund',
        'LOP': 'Loss of Pay',
        'LOAN': 'Loan Recovery',
        'ADV': 'Advance Recovery',
    }

    class Meta:
        db_table = 'hr_salary_components'
        ordering = ['component_type', 'display_order']

    def __str__(self):
        return f"{self.code} - {self.name}"


class EmployeeSalary(models.Model):
    SALARY_TYPE_CHOICES = [
        ('monthly', 'Monthly'), ('daily', 'Daily'), ('hourly', 'Hourly'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='salary_records')
    salary_structure = models.ForeignKey(SalaryStructure, on_delete=models.PROTECT)
    ctc = models.DecimalField(max_digits=12, decimal_places=2, help_text='Cost to Company annually')
    monthly_ctc = models.DecimalField(max_digits=12, decimal_places=2)
    basic = models.DecimalField(max_digits=12, decimal_places=2)
    hra = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    special_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    medical_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    conveyance_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_allowances = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gross_salary = models.DecimalField(max_digits=12, decimal_places=2)
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    salary_type = models.CharField(max_length=10, choices=SALARY_TYPE_CHOICES, default='monthly')
    revision_reason = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    revised_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'hr_employee_salaries'
        ordering = ['-effective_from']

    def __str__(self):
        return f"{self.employee} - {self.monthly_ctc} - {self.effective_from}"


class PayrollPeriod(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'), ('processing', 'Processing'),
        ('processed', 'Processed'), ('approved', 'Approved'),
        ('released', 'Released'), ('paid', 'Paid'), ('locked', 'Locked'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    month = models.PositiveIntegerField()
    year = models.PositiveIntegerField()
    from_date = models.DateField()
    to_date = models.DateField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')
    total_employees = models.PositiveIntegerField(default=0)
    total_gross = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_net = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    processed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                      on_delete=models.SET_NULL, related_name='processed_payrolls')
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                     on_delete=models.SET_NULL, related_name='approved_payrolls')
    released_at = models.DateTimeField(null=True, blank=True)
    released_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name='released_payrolls')
    paid_at = models.DateTimeField(null=True, blank=True)
    paid_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                on_delete=models.SET_NULL, related_name='paid_payrolls')
    locked_at = models.DateTimeField(null=True, blank=True)
    locked_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                  on_delete=models.SET_NULL, related_name='locked_payrolls')
    rejection_reason = models.TextField(blank=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'hr_payroll_periods'
        unique_together = ['month', 'year']
        ordering = ['-year', '-month']

    def __str__(self):
        return self.name


class PayslipRecord(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'), ('generated', 'Generated'),
        ('approved', 'Approved'), ('released', 'Released'), ('paid', 'Paid'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payroll_period = models.ForeignKey(PayrollPeriod, on_delete=models.CASCADE, related_name='payslips')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payslips')
    payslip_number = models.CharField(max_length=30, unique=True)

    # Attendance data
    total_working_days = models.PositiveIntegerField(default=0)
    days_present = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    days_absent = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    days_on_leave = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    days_lop = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    overtime_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    # Earnings
    basic = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    hra = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    special_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    medical_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    conveyance_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bonus = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    overtime_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    arrears = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gross_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Deductions
    pf_employee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    pf_employer = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    esi_employee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    esi_employer = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    professional_tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tds = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    lwf_employee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    lwf_employer = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    loan_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    advance_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    lop_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Net
    net_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    calculation_details = models.JSONField(default=dict, blank=True)

    # Payslip file
    payslip_pdf = models.FileField(upload_to='payslips/', null=True, blank=True)
    released_at = models.DateTimeField(null=True, blank=True)
    released_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name='released_payslips')
    is_email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)

    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')
    payment_date = models.DateField(null=True, blank=True)
    payment_mode = models.CharField(max_length=50, blank=True)
    bank_reference = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'hr_payslips'
        unique_together = ['payroll_period', 'employee']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['employee', 'payroll_period']),
        ]

    def __str__(self):
        return f"{self.payslip_number} - {self.employee} - {self.payroll_period}"

    def save(self, *args, **kwargs):
        if not self.payslip_number:
            period = self.payroll_period
            emp = self.employee
            self.payslip_number = f"PS{period.year}{str(period.month).zfill(2)}{emp.employee_code}"
        super().save(*args, **kwargs)


class LoanRecord(models.Model):
    LOAN_TYPE_CHOICES = [
        ('personal', 'Personal Loan'), ('vehicle', 'Vehicle Loan'),
        ('housing', 'Housing Loan'), ('education', 'Education Loan'),
        ('advance', 'Salary Advance'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'), ('approved', 'Approved'),
        ('rejected', 'Rejected'), ('active', 'Active'),
        ('closed', 'Closed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='loans')
    loan_type = models.CharField(max_length=15, choices=LOAN_TYPE_CHOICES)
    loan_amount = models.DecimalField(max_digits=12, decimal_places=2)
    outstanding_amount = models.DecimalField(max_digits=12, decimal_places=2)
    monthly_installment = models.DecimalField(max_digits=12, decimal_places=2)
    disbursed_date = models.DateField(null=True, blank=True)
    start_deduction_month = models.DateField()
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    reason = models.TextField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                     on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'hr_loans'
