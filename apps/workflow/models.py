import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.employees.models import Department, Designation, Employee


class ApprovalModule(models.Model):
    MODULE_CHOICES = [
        ('leave', 'Leave'),
        ('attendance', 'Attendance'),
        ('swipe_request', 'Swipe Request'),
        ('exit_route', 'Exit Route'),
        ('short_time_off', 'Short Time Off'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, choices=MODULE_CHOICES, unique=True)
    label = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'workflow_approval_modules'
        ordering = ['label']

    def __str__(self):
        return self.label


class ApprovalRule(models.Model):
    APPROVER_ROLE_CHOICES = [
        ('manager', 'Manager'),
        ('reporting_manager', 'Reporting Manager'),
        ('department_head', 'Department Head'),
        ('hr_admin', 'HR Admin'),
        ('super_admin', 'Super Admin'),
        ('finance', 'Finance'),
        ('custom_user', 'Specific User'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(ApprovalModule, on_delete=models.CASCADE, related_name='rules')
    level_number = models.PositiveIntegerField(default=1)
    name = models.CharField(max_length=50)
    approver_role = models.CharField(max_length=30, choices=APPROVER_ROLE_CHOICES, default='manager')
    is_required = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'workflow_approval_rules'
        unique_together = ('module', 'level_number', 'name')
        ordering = ['module', 'level_number']

    def __str__(self):
        return f'{self.module.label} - {self.name}'


class ApprovalAssignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(ApprovalModule, on_delete=models.CASCADE, related_name='assignments')
    rule = models.ForeignKey(ApprovalRule, on_delete=models.CASCADE, related_name='assignments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                            related_name='approval_assignments')
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL,
                                  related_name='approval_assignments')
    designation = models.ForeignKey(Designation, null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name='approval_assignments')
    employee = models.ForeignKey(Employee, null=True, blank=True, on_delete=models.SET_NULL,
                                related_name='approval_assignments')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'workflow_approval_assignments'
        ordering = ['module', 'rule__level_number']

    def __str__(self):
        label = self.user.email if self.user else self.employee.get_full_name() if self.employee else 'Assignment'
        return f'{self.module.label} - {self.rule.name} - {label}'


class SwipeRequest(models.Model):
    REQUEST_TYPE_CHOICES = [
        ('in', 'Missing In'),
        ('out', 'Missing Out'),
        ('both', 'Missing In and Out'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='swipe_requests')
    attendance = models.ForeignKey('attendance.Attendance', on_delete=models.CASCADE, related_name='swipe_requests', null=True, blank=True)
    request_type = models.CharField(max_length=10, choices=REQUEST_TYPE_CHOICES)
    requested_in = models.DateTimeField(null=True, blank=True)
    requested_out = models.DateTimeField(null=True, blank=True)
    reason = models.TextField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    current_level = models.PositiveIntegerField(default=1)
    current_approver = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                        on_delete=models.SET_NULL, related_name='swipe_requests_to_approve')
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name='swipe_reviews')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewer_remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'workflow_swipe_requests'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.employee} - {self.request_type} - {self.status}'

    def get_approver_for_level(self, level_number):
        module = ApprovalModule.objects.filter(name='swipe_request').first()
        if not module:
            return None
        rule = ApprovalRule.objects.filter(module=module, level_number=level_number, is_active=True).first()
        if not rule:
            return None

        assignment = ApprovalAssignment.objects.filter(module=module, rule=rule, is_active=True).first()
        if not assignment:
            return None

        if assignment.user:
            return assignment.user
        if assignment.employee:
            return assignment.employee.user
        if assignment.department:
            try:
                manager_emp = self.employee.reporting_manager
                if manager_emp and manager_emp.department == assignment.department:
                    return manager_emp.user
            except Exception:
                pass
        return None

    def approve(self, approver_user):
        if self.status != 'pending':
            return False

        self.status = 'approved'
        self.reviewed_by = approver_user
        self.reviewed_at = timezone.now()
        self.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'updated_at'])

        if self.attendance is not None:
            if self.request_type in ('in', 'both') and self.requested_in:
                self.attendance.clock_in = self.requested_in
            if self.request_type in ('out', 'both') and self.requested_out:
                self.attendance.clock_out = self.requested_out

            self.attendance.approval_status = 'approved'
            self.attendance.approved_by = approver_user
            self.attendance.approved_at = timezone.now()

            if self.attendance.clock_in and self.attendance.clock_out:
                self.attendance.status = 'present'
                self.attendance.save(update_fields=['clock_in', 'clock_out', 'status', 'approval_status', 'approved_by', 'approved_at'])
            else:
                self.attendance.save(update_fields=['clock_in', 'clock_out', 'approval_status', 'approved_by', 'approved_at'])

        return True

    def reject(self, approver_user, remarks=''):
        self.status = 'rejected'
        self.reviewed_by = approver_user
        self.reviewed_at = timezone.now()
        self.reviewer_remarks = remarks
        self.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'reviewer_remarks', 'updated_at'])
        return True


class ApprovalWorkflow(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(ApprovalModule, on_delete=models.CASCADE, related_name='workflow_records')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='approval_workflows')
    current_level = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'workflow_approval_records'

    def __str__(self):
        return f'{self.module.label} - {self.employee}'
