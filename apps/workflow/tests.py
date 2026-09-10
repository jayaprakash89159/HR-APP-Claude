from django.test import TestCase
from django.utils import timezone

from apps.attendance.models import Attendance
from apps.employees.models import Department, Designation, Location, Employee, CostCenter
from apps.workflow.models import ApprovalModule, ApprovalAssignment, ApprovalRule, SwipeRequest
from apps.authentication.models import User


class ApprovalWorkflowTests(TestCase):
    def setUp(self):
        self.department = Department.objects.create(name='Engineering', code='ENG', description='Engineering')
        self.location = Location.objects.create(
            name='HQ', code='HQ1', address='Main Street', city='Hyderabad', state='TS',
            country='India', pincode='500001', geo_fence_radius=200,
        )
        self.designation = Designation.objects.create(
            name='Software Engineer', department=self.department, grade='G1', level=1,
        )
        self.cost_center = CostCenter.objects.create(name='Product', code='PC1', department=self.department)

        self.manager_user = User.objects.create_user(email='manager@example.com', password='Password123!')
        self.manager_user.role = 'manager'
        self.manager_user.save()

        self.employee_user = User.objects.create_user(email='employee@example.com', password='Password123!')
        self.employee_user.role = 'employee'
        self.employee_user.save()

        self.manager_employee = Employee.objects.create(
            user=self.manager_user,
            employee_id='EMP1000', employee_code='EMP1000', first_name='Manager', last_name='One',
            official_email='manager@company.com', personal_email='mgr@company.com', mobile='9000000000',
            gender='M', date_of_birth='1990-01-01', joining_date='2020-01-01', department=self.department,
            designation=self.designation, location=self.location, cost_center=self.cost_center,
        )

        self.employee = Employee.objects.create(
            user=self.employee_user,
            employee_id='EMP1001', employee_code='EMP1001', first_name='Employee', last_name='One',
            official_email='employee@company.com', personal_email='emp@company.com', mobile='9000000001',
            gender='M', date_of_birth='1992-01-01', joining_date='2022-01-01', department=self.department,
            designation=self.designation, location=self.location, reporting_manager=self.manager_employee,
            cost_center=self.cost_center,
        )

        self.module = ApprovalModule.objects.create(name='swipe_request', label='Swipe Request')
        self.rule = ApprovalRule.objects.create(module=self.module, level_number=1, name='L1', approver_role='manager')
        ApprovalAssignment.objects.create(module=self.module, rule=self.rule, user=self.manager_user)

    def test_swipe_request_approval_marks_attendance_present(self):
        attendance = Attendance.objects.create(
            employee=self.employee,
            date=timezone.now().date(),
            status='absent',
            clock_in=None,
            clock_out=None,
            approval_status='pending',
        )

        swipe_request = SwipeRequest.objects.create(
            employee=self.employee,
            attendance=attendance,
            request_type='both',
            reason='Forgot both punches',
            status='pending',
        )

        swipe_request.approve(self.manager_user)

        attendance.refresh_from_db()
        self.assertEqual(swipe_request.status, 'approved')
        self.assertEqual(attendance.status, 'present')
        self.assertEqual(attendance.approval_status, 'approved')

    def test_approval_flow_admin_dashboard_is_available(self):
        self.client.force_login(self.manager_user)
        response = self.client.get('/admin/workflow/approvalmodule/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Approval Flow Configuration')
        self.assertContains(response, 'Set approval modules, rules, and assignees for leave and attendance requests.')
