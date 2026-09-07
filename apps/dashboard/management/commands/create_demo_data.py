"""
WorkSphere HR - create_demo_data management command
Creates complete demo data for testing
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
import random


class Command(BaseCommand):
    help = 'Create demo data for WorkSphere HR'

    def handle(self, *args, **options):
        self.stdout.write('🔧 Setting up demo data...')
        try:
            self._create_users()
            self._create_org_structure()
            self._create_employees()
            self._create_shifts()
            self._create_leave_types()
            self._create_holidays()
            self._create_attendance()
            self._create_leave_applications()
            self.stdout.write(self.style.SUCCESS('✅ Demo data ready!'))
            self.stdout.write('')
            self.stdout.write('━' * 50)
            self.stdout.write('  Login Credentials:')
            self.stdout.write('  Super Admin : admin@worksphere.hr / Admin@123')
            self.stdout.write('  HR Admin    : hr@worksphere.hr    / Admin@123')
            self.stdout.write('  Manager     : manager@worksphere.hr / Mgr@123')
            self.stdout.write('  Employee    : employee@worksphere.hr / Emp@123')
            self.stdout.write('━' * 50)
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'ℹ️  Demo data: {e}'))

    def _create_users(self):
        from apps.authentication.models import User
        users = [
            {'email': 'admin@worksphere.hr',    'password': 'Admin@123', 'role': 'super_admin',   'is_staff': True, 'is_superuser': True},
            {'email': 'hr@worksphere.hr',        'password': 'Admin@123', 'role': 'hr_admin',      'is_staff': True},
            {'email': 'payroll@worksphere.hr',   'password': 'Pay@123',   'role': 'payroll_admin', 'is_staff': True},
            {'email': 'manager@worksphere.hr',   'password': 'Mgr@123',   'role': 'manager'},
            {'email': 'employee@worksphere.hr',  'password': 'Emp@123',   'role': 'employee'},
        ]
        for u in users:
            if not User.objects.filter(email=u['email']).exists():
                User.objects.create_user(
                    email=u['email'], password=u['password'], role=u['role'],
                    is_staff=u.get('is_staff', False),
                    is_superuser=u.get('is_superuser', False),
                )
                self.stdout.write(f'  + User: {u["email"]}')

    def _create_org_structure(self):
        from apps.employees.models import Department, Designation, Location, CostCenter

        if not Location.objects.exists():
            Location.objects.create(
                name='Head Office', code='HO',
                address='Tech Park, Whitefield', city='Bangalore',
                state='Karnataka', country='India', pincode='560066',
                latitude=12.9716, longitude=77.5946, geo_fence_radius=300,
            )

        depts = {}
        for name, code in [('Engineering','ENG'),('Human Resources','HR'),('Finance','FIN'),('Sales','SAL')]:
            d, _ = Department.objects.get_or_create(code=code, defaults={'name': name})
            depts[code] = d

        for name, dept_code, grade, level in [
            ('Software Engineer',      'ENG', 'L2', 2),
            ('Senior Engineer',        'ENG', 'L3', 3),
            ('Engineering Manager',    'ENG', 'L5', 5),
            ('HR Executive',           'HR',  'L2', 2),
            ('HR Manager',             'HR',  'L4', 4),
            ('Financial Analyst',      'FIN', 'L2', 2),
            ('Sales Executive',        'SAL', 'L2', 2),
        ]:
            Designation.objects.get_or_create(
                name=name, department=depts[dept_code],
                defaults={'grade': grade, 'level': level}
            )

        for name, code in [('Technology','CC-TECH'),('HR','CC-HR')]:
            CostCenter.objects.get_or_create(code=code, defaults={'name': name})

    def _create_employees(self):
        from apps.authentication.models import User
        from apps.employees.models import Employee, Department, Designation, Location, EmployeeStatutory

        if Employee.objects.count() >= 4:
            return

        loc = Location.objects.get(code='HO')
        dept_eng = Department.objects.get(code='ENG')
        dept_hr  = Department.objects.get(code='HR')
        desig_mgr = Designation.objects.get(name='Engineering Manager')
        desig_swe = Designation.objects.get(name='Software Engineer')
        desig_hr  = Designation.objects.get(name='HR Executive')

        data = [
            ('admin@worksphere.hr',   'Arjun',  'Sharma', 'EMP001', 'WS-001', 'M', date(1990,5,15),  date(2020,1,1),  dept_eng, desig_mgr),
            ('manager@worksphere.hr', 'Priya',  'Nair',   'EMP002', 'WS-002', 'F', date(1992,8,20),  date(2021,3,15), dept_eng, desig_swe),
            ('hr@worksphere.hr',      'Kavitha','Reddy',  'EMP003', 'WS-003', 'F', date(1993,3,10),  date(2021,6,1),  dept_hr,  desig_hr),
            ('employee@worksphere.hr','Rahul',  'Kumar',  'EMP004', 'WS-004', 'M', date(1995,11,25), date(2022,9,1),  dept_eng, desig_swe),
        ]

        created_emps = []
        for email, fname, lname, ecode, eid, gender, dob, joining, dept, desig in data:
            try:
                user = User.objects.get(email=email)
                emp, created = Employee.objects.get_or_create(
                    employee_code=ecode,
                    defaults={
                        'user': user, 'employee_id': eid,
                        'first_name': fname, 'last_name': lname,
                        'official_email': email, 'mobile': f'98765432{len(created_emps)}0',
                        'gender': gender, 'date_of_birth': dob,
                        'joining_date': joining, 'department': dept,
                        'designation': desig, 'location': loc,
                    }
                )
                if created:
                    EmployeeStatutory.objects.get_or_create(employee=emp)
                    self.stdout.write(f'  + Employee: {fname} {lname}')
                created_emps.append(emp)
            except Exception as e:
                self.stdout.write(f'  ! Skip {email}: {e}')

        # Set reporting manager
        if len(created_emps) >= 2:
            mgr = created_emps[0]
            for emp in created_emps[1:]:
                if not emp.reporting_manager:
                    emp.reporting_manager = mgr
                    emp.save(update_fields=['reporting_manager'])

    def _create_shifts(self):
        from apps.shifts.models import Shift
        from datetime import time

        shifts = [
            {'name': 'General Shift', 'code': 'GEN', 'shift_type': 'general',
             'start_time': time(9,0),  'end_time': time(18,0),
             'working_days': [0,1,2,3,4], 'week_off_days': [5,6],
             'grace_period_minutes': 15, 'full_day_hours': 8.0, 'minimum_hours': 4.0},
        ]
        for s in shifts:
            Shift.objects.get_or_create(code=s['code'], defaults=s)

    def _create_leave_types(self):
        from apps.leave_management.models import LeaveType, LeaveBalance
        from apps.employees.models import Employee

        types = [
            {'name': 'Casual Leave',    'code': 'CL',  'category': 'casual',      'days_allowed_per_year': 12, 'color': '#2563EB', 'allow_half_day': True,  'is_paid': True},
            {'name': 'Sick Leave',      'code': 'SL',  'category': 'sick',        'days_allowed_per_year': 10, 'color': '#10B981', 'allow_half_day': True,  'is_paid': True},
            {'name': 'Earned Leave',    'code': 'EL',  'category': 'earned',      'days_allowed_per_year': 15, 'color': '#F59E0B', 'allow_half_day': True,  'is_paid': True, 'is_encashable': True},
            {'name': 'Comp Off',        'code': 'CO',  'category': 'comp_off',    'days_allowed_per_year': 5,  'color': '#8B5CF6', 'allow_half_day': True,  'is_paid': True},
            {'name': 'Loss Of Pay',     'code': 'LOP', 'category': 'loss_of_pay', 'days_allowed_per_year': 30, 'color': '#EF4444', 'allow_half_day': False, 'is_paid': False},
        ]

        year = timezone.now().year
        employees = list(Employee.objects.filter(status='active'))

        for t in types:
            lt, created = LeaveType.objects.get_or_create(code=t['code'], defaults=t)
            if created:
                for emp in employees:
                    availed = round(random.uniform(0, float(t['days_allowed_per_year']) * 0.3), 1)
                    LeaveBalance.objects.get_or_create(
                        employee=emp, leave_type=lt, year=year,
                        defaults={'entitled_days': t['days_allowed_per_year'], 'availed': availed}
                    )

    def _create_holidays(self):
        from apps.leave_management.models import HolidayCalendar
        year = timezone.now().year
        holidays = [
            ('Republic Day',      date(year, 1, 26), 'national'),
            ('Independence Day',  date(year, 8, 15), 'national'),
            ('Gandhi Jayanti',    date(year, 10, 2), 'national'),
            ('Diwali',            date(year, 10, 20),'national'),
            ('Christmas',         date(year, 12, 25),'national'),
        ]
        for name, hdate, htype in holidays:
            HolidayCalendar.objects.get_or_create(
                date=hdate,
                defaults={'name': name, 'holiday_type': htype, 'year': year}
            )

    def _create_attendance(self):
        from apps.attendance.models import Attendance
        from apps.employees.models import Employee
        from apps.shifts.models import Shift

        today = timezone.now().date()
        demo_codes = ['EMP001', 'EMP002', 'EMP003', 'EMP004']
        employees = list(Employee.objects.filter(status='active', employee_code__in=demo_codes))

        try:
            shift = Shift.objects.get(code='GEN')
        except Shift.DoesNotExist:
            return

        for emp in employees:
            for i in range(30, 0, -1):
                day = today - timedelta(days=i)
                if day.weekday() >= 5:
                    Attendance.objects.get_or_create(
                        employee=emp, date=day,
                        defaults={'status': 'week_off', 'shift': shift}
                    )
                    continue

                rand = random.random()
                if rand > 0.93:
                    Attendance.objects.get_or_create(employee=emp, date=day, defaults={'status': 'absent'})
                elif rand > 0.85:
                    Attendance.objects.get_or_create(employee=emp, date=day, defaults={'status': 'leave'})
                else:
                    late_mins = random.randint(-5, 25)
                    from datetime import datetime
                    base_in = timezone.make_aware(datetime(day.year, day.month, day.day, 9, 0))
                    clock_in = base_in + timedelta(minutes=late_mins)
                    hours = random.uniform(7.5, 9.0)
                    clock_out = clock_in + timedelta(hours=hours)
                    status = 'late_mark' if late_mins > 15 else 'present'
                    total_mins = int(hours * 60)
                    Attendance.objects.get_or_create(
                        employee=emp, date=day,
                        defaults={
                            'status': status, 'shift': shift,
                            'clock_in': clock_in, 'clock_out': clock_out,
                            'total_working_minutes': total_mins,
                            'effective_working_minutes': total_mins,
                            'late_minutes': max(0, late_mins - 15),
                            'clock_in_source': 'web', 'clock_out_source': 'web',
                        }
                    )

    def _create_leave_applications(self):
        from apps.leave_management.models import LeaveApplication, LeaveType
        from apps.employees.models import Employee
        try:
            emp = Employee.objects.get(employee_code='EMP004')
            lt  = LeaveType.objects.get(code='CL')
            today = timezone.now().date()
            if not LeaveApplication.objects.filter(employee=emp).exists():
                LeaveApplication.objects.create(
                    employee=emp, leave_type=lt,
                    from_date=today + timedelta(days=5),
                    to_date=today + timedelta(days=6),
                    total_days=2, reason='Personal work', status='pending',
                )
        except Exception:
            pass
