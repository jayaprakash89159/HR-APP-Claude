"""
WorkSphere HR - Leave Management Models
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.employees.models import Employee
import uuid


class LeaveType(models.Model):
    LEAVE_CATEGORY_CHOICES = [
        ('casual', 'Casual Leave'),
        ('sick', 'Sick Leave'),
        ('earned', 'Earned Leave'),
        ('comp_off', 'Comp Off'),
        ('maternity', 'Maternity Leave'),
        ('paternity', 'Paternity Leave'),
        ('bereavement', 'Bereavement Leave'),
        ('loss_of_pay', 'Loss Of Pay'),
        ('optional', 'Optional Holiday'),
        ('other', 'Other'),
    ]
    ACCRUAL_TYPE_CHOICES = [
        ('fixed', 'Fixed'), ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'), ('yearly', 'Yearly'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    category = models.CharField(max_length=20, choices=LEAVE_CATEGORY_CHOICES)
    color = models.CharField(max_length=7, default='#2563EB')
    days_allowed_per_year = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    max_carry_forward = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    min_balance_for_encashment = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    is_paid = models.BooleanField(default=True)
    is_encashable = models.BooleanField(default=False)
    is_carry_forwardable = models.BooleanField(default=False)
    allow_half_day = models.BooleanField(default=True)
    min_days = models.DecimalField(max_digits=4, decimal_places=1, default=0.5)
    max_days = models.DecimalField(max_digits=4, decimal_places=1, default=30)
    advance_days_required = models.PositiveIntegerField(default=0)
    requires_document = models.BooleanField(default=False)
    accrual_type = models.CharField(max_length=15, choices=ACCRUAL_TYPE_CHOICES, default='yearly')
    gender_specific = models.CharField(max_length=1, blank=True, help_text='M=Male, F=Female, blank=All')
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'hr_leave_types'
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class LeaveBalance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_balances')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE, related_name='balances')
    year = models.PositiveIntegerField()
    entitled_days = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    carried_forward = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    accrued = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    availed = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    lapsed = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    encashed = models.DecimalField(max_digits=5, decimal_places=1, default=0)

    class Meta:
        db_table = 'hr_leave_balances'
        unique_together = ['employee', 'leave_type', 'year']

    def __str__(self):
        return f"{self.employee} - {self.leave_type} - {self.year}"

    @property
    def available_days(self):
        return self.entitled_days + self.carried_forward + self.accrued - self.availed - self.encashed


class LeaveApplication(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
        ('lapsed', 'Lapsed'),
    ]
    DAY_TYPE_CHOICES = [
        ('full_day', 'Full Day'),
        ('first_half', 'First Half'),
        ('second_half', 'Second Half'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application_number = models.CharField(max_length=20, unique=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_applications')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    from_date = models.DateField()
    to_date = models.DateField()
    from_day_type = models.CharField(max_length=15, choices=DAY_TYPE_CHOICES, default='full_day')
    to_day_type = models.CharField(max_length=15, choices=DAY_TYPE_CHOICES, default='full_day')
    total_days = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    reason = models.TextField()
    document = models.FileField(upload_to='leave/documents/', null=True, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    current_approval_level = models.PositiveIntegerField(default=1)

    # Manager approval
    manager_status = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True)
    manager_reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                             on_delete=models.SET_NULL, related_name='manager_leave_reviews')
    manager_reviewed_at = models.DateTimeField(null=True, blank=True)
    manager_remarks = models.TextField(blank=True)

    # HR approval
    hr_status = models.CharField(max_length=15, choices=STATUS_CHOICES, blank=True)
    hr_reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                        on_delete=models.SET_NULL, related_name='hr_leave_reviews')
    hr_reviewed_at = models.DateTimeField(null=True, blank=True)
    hr_remarks = models.TextField(blank=True)

    # Cancellation
    cancellation_reason = models.TextField(blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'hr_leave_applications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['from_date', 'to_date']),
        ]

    def __str__(self):
        return f"{self.application_number} - {self.employee} - {self.leave_type}"

    def approve_by_level(self, approver, level_number, remarks=''):
        if level_number == 1:
            self.manager_status = 'approved'
            self.manager_reviewed_by = approver
            self.manager_reviewed_at = timezone.now()
            self.manager_remarks = remarks
            self.current_approval_level = 2
            if self.hr_status == 'approved':
                self.status = 'approved'
            else:
                self.status = 'pending'
        elif level_number == 2:
            self.hr_status = 'approved'
            self.hr_reviewed_by = approver
            self.hr_reviewed_at = timezone.now()
            self.hr_remarks = remarks
            self.current_approval_level = 2
            self.status = 'approved' if self.manager_status == 'approved' else 'pending'
        else:
            self.status = 'approved'
        self.save()
        return self

    def reject_by_level(self, approver, level_number, remarks=''):
        if level_number == 1:
            self.manager_status = 'rejected'
            self.manager_reviewed_by = approver
            self.manager_reviewed_at = timezone.now()
            self.manager_remarks = remarks
        elif level_number == 2:
            self.hr_status = 'rejected'
            self.hr_reviewed_by = approver
            self.hr_reviewed_at = timezone.now()
            self.hr_remarks = remarks
        self.status = 'rejected'
        self.save()
        return self

    def save(self, *args, **kwargs):
        if not self.application_number:
            import datetime
            self.application_number = f"LA{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        super().save(*args, **kwargs)


class HolidayCalendar(models.Model):
    HOLIDAY_TYPE_CHOICES = [
        ('national', 'National Holiday'),
        ('state', 'State Holiday'),
        ('company', 'Company Holiday'),
        ('optional', 'Optional Holiday'),
        ('religious', 'Religious Holiday'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    date = models.DateField()
    holiday_type = models.CharField(max_length=15, choices=HOLIDAY_TYPE_CHOICES)
    year = models.PositiveIntegerField()
    is_optional = models.BooleanField(default=False)
    location = models.ForeignKey('employees.Location', null=True, blank=True, on_delete=models.SET_NULL)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'hr_holiday_calendar'
        ordering = ['date']
        unique_together = ['date', 'location']

    def __str__(self):
        return f"{self.name} - {self.date}"


class LeaveCancellation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    leave_application = models.ForeignKey(LeaveApplication, on_delete=models.CASCADE,
                                           related_name='cancellations')
    reason = models.TextField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                     on_delete=models.SET_NULL)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'hr_leave_cancellations'
