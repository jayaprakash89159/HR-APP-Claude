from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.db.models import Q

from apps.attendance.models import Attendance
from apps.employees.models import Employee
from apps.leave_management.models import HolidayCalendar, LeaveApplication

from ..models import EmployeeSalary, PayslipRecord, PayrollPeriod
from .statutory import calculate_statutory
from .formula import UnsafeFormulaError, evaluate_formula


CENT = Decimal('0.01')


class PayrollCalculationError(Exception):
    def __init__(self, message, details=None):
        super().__init__(message)
        self.details = details or {}


def process_payroll_period(period_id, user):
    """Calculate a draft period from approved source records and create payslips."""
    with transaction.atomic():
        period = PayrollPeriod.objects.select_for_update().get(pk=period_id)
        if period.status != 'processing':
            raise PayrollCalculationError(f'Only processing periods can be calculated; current status is {period.status}.')

        employees = Employee.objects.filter(status='active').order_by('employee_code')
        holidays = set(HolidayCalendar.objects.filter(
            date__range=(period.from_date, period.to_date), is_active=True
        ).values_list('date', flat=True))
        working_dates = _working_dates(period.from_date, period.to_date, holidays)
        errors = []
        calculated = []

        for employee in employees:
            salary = _salary_for_period(employee, period)
            if salary is None:
                errors.append({'employee_id': str(employee.id), 'employee_code': employee.employee_code, 'error': 'No effective salary record.'})
                continue
            try:
                calculated.append(_calculate_employee(employee, salary, period, working_dates))
            except UnsafeFormulaError as exc:
                errors.append({'employee_id': str(employee.id), 'employee_code': employee.employee_code, 'error': str(exc)})

        if errors:
            raise PayrollCalculationError('Payroll cannot be calculated because salary data is missing.', {'employees': errors})

        PayslipRecord.objects.filter(payroll_period=period, status__in=('draft', 'generated')).delete()
        for result in calculated:
            PayslipRecord.objects.create(payroll_period=period, employee=result.pop('employee'), status='generated', **result)

        period.total_employees = len(calculated)
        period.total_gross = sum((p.gross_earnings for p in PayslipRecord.objects.filter(payroll_period=period)), Decimal('0'))
        period.total_deductions = sum((p.total_deductions for p in PayslipRecord.objects.filter(payroll_period=period)), Decimal('0'))
        period.total_net = sum((p.net_salary for p in PayslipRecord.objects.filter(payroll_period=period)), Decimal('0'))
        period.status = 'processed'
        period.processed_by = user
        from django.utils import timezone
        period.processed_at = timezone.now()
        period.save(update_fields=['total_employees', 'total_gross', 'total_deductions', 'total_net', 'status', 'processed_by', 'processed_at'])
        return period


def _calculate_employee(employee, salary, period, working_dates):
    attendance = Attendance.objects.filter(
        employee=employee, date__range=(period.from_date, period.to_date), approval_status='approved'
    )
    attendance_by_date = {record.date: record for record in attendance}
    leave = LeaveApplication.objects.filter(
        employee=employee, status='approved', from_date__lte=period.to_date, to_date__gte=period.from_date
    ).select_related('leave_type')
    leave_dates = {}
    for application in leave:
        current = max(application.from_date, period.from_date)
        end = min(application.to_date, period.to_date)
        while current <= end:
            if current in working_dates:
                leave_dates[current] = application.leave_type.category
            current += timedelta(days=1)

    present = Decimal('0')
    half_days = Decimal('0')
    paid_leave = Decimal('0')
    lop_leave = Decimal('0')
    overtime_minutes = 0
    absent = Decimal('0')
    for current in working_dates:
        record = attendance_by_date.get(current)
        if record and record.status == 'half_day':
            half_days += Decimal('0.5')
        elif record and record.status in ('present', 'late_mark', 'on_duty', 'work_from_home', 'comp_off'):
            present += Decimal('1')
        elif current in leave_dates:
            if leave_dates[current] == 'loss_of_pay':
                lop_leave += Decimal('1')
            else:
                paid_leave += Decimal('1')
        else:
            absent += Decimal('1')
        if record:
            overtime_minutes += record.overtime_minutes or 0

    payable_days = present + half_days + paid_leave
    lop_days = lop_leave + absent + (half_days * Decimal('0.5'))
    working_days = Decimal(len(working_dates))
    monthly_factor = payable_days / working_days if working_days else Decimal('0')
    monthly_ctc = Decimal(salary.monthly_ctc)
    basic = _money(Decimal(salary.basic) * monthly_factor)
    hra = _money(Decimal(salary.hra) * monthly_factor)
    special = _money(Decimal(salary.special_allowance) * monthly_factor)
    medical = _money(Decimal(salary.medical_allowance) * monthly_factor)
    conveyance = _money(Decimal(salary.conveyance_allowance) * monthly_factor)
    gross = _money(basic + hra + special + medical + conveyance)
    structure_earnings, structure_deductions, structure_details = _calculate_structure_components(
        salary, basic, monthly_ctc, gross
    )
    other_earnings = _money(structure_earnings)
    gross = _money(gross + other_earnings)
    lop_amount = _money(monthly_ctc * (lop_days / working_days)) if working_days else Decimal('0')
    statutory = calculate_statutory(employee, basic, gross)
    other_deductions = _money(structure_deductions)
    total_deductions = _money(lop_amount + other_deductions + statutory['pf_employee'] + statutory['esi_employee'] + statutory['professional_tax'] + statutory['tds'] + statutory['lwf_employee'])
    net = _money(gross - total_deductions)

    return {
        'employee': employee,
        'total_working_days': len(working_dates),
        'days_present': present + half_days,
        'days_absent': absent,
        'days_on_leave': paid_leave,
        'days_lop': lop_days,
        'overtime_hours': _money(Decimal(overtime_minutes) / Decimal('60')),
        'basic': basic,
        'hra': hra,
        'special_allowance': special,
        'medical_allowance': medical,
        'conveyance_allowance': conveyance,
        'gross_earnings': gross,
        'other_earnings': other_earnings,
        'pf_employee': statutory['pf_employee'],
        'pf_employer': statutory['pf_employer'],
        'esi_employee': statutory['esi_employee'],
        'esi_employer': statutory['esi_employer'],
        'professional_tax': statutory['professional_tax'],
        'tds': statutory['tds'],
        'lwf_employee': statutory['lwf_employee'],
        'lwf_employer': statutory['lwf_employer'],
        'other_deductions': other_deductions,
        'lop_amount': lop_amount,
        'total_deductions': total_deductions,
        'net_salary': net,
        'calculation_details': {
            'source': 'approved_attendance_and_leave',
            'working_days': len(working_dates),
            'present_days': str(present),
            'half_days': str(half_days),
            'paid_leave_days': str(paid_leave),
            'lop_days': str(lop_days),
            'overtime_minutes': overtime_minutes,
            'monthly_factor': str(monthly_factor),
            'statutory_rules': 'Not configured; no statutory deductions were assumed.',
            'statutory': statutory['details'],
            'salary_structure_components': structure_details,
        },
    }


def _salary_for_period(employee, period):
    return EmployeeSalary.objects.filter(
        employee=employee, is_active=True, effective_from__lte=period.to_date
    ).filter(Q(effective_to__isnull=True) | Q(effective_to__gte=period.from_date)).order_by('-effective_from').first()


def _calculate_structure_components(salary, basic, monthly_ctc, gross):
    earnings = Decimal('0')
    deductions = Decimal('0')
    details = []
    known_codes = {'BASIC', 'HRA', 'SPEC', 'MED', 'CONV'}
    context = {'basic': basic, 'monthly_ctc': monthly_ctc, 'gross': gross}
    for assignment in salary.salary_structure.components.select_related('component').filter(is_active=True):
        component = assignment.component
        if component.code.upper() in known_codes:
            continue
        if component.calculation_type == 'fixed':
            amount = Decimal(component.fixed_amount)
        elif component.calculation_type == 'percentage':
            amount = basic * Decimal(component.percentage) / Decimal('100')
        elif component.calculation_type == 'percentage_ctc':
            amount = monthly_ctc * Decimal(component.percentage) / Decimal('100')
        elif component.calculation_type == 'formula':
            amount = evaluate_formula(component.formula, context)
        else:
            amount = Decimal('0')
        amount = _money(amount)
        if component.component_type == 'earning':
            earnings += amount
        else:
            deductions += amount
        details.append({'code': component.code, 'type': component.component_type, 'amount': str(amount)})
    return earnings, deductions, details


def _working_dates(start, end, holidays):
    dates = []
    current = start
    while current <= end:
        if current.weekday() < 5 and current not in holidays:
            dates.append(current)
        current += timedelta(days=1)
    return dates


def _money(value):
    return value.quantize(CENT, rounding=ROUND_HALF_UP)