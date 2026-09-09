"""
WorkSphere HR - Dashboard Views
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime, timedelta
import calendar
import json

from apps.employees.models import Employee, Department
from apps.attendance.models import Attendance
from apps.leave_management.models import LeaveBalance, LeaveApplication, HolidayCalendar
from apps.notifications.models import Notification


def get_greeting():
    hour = timezone.now().hour
    if hour < 12:
        return "Morning"
    elif hour < 17:
        return "Afternoon"
    else:
        return "Evening"


@login_required
def home(request):
    user = request.user
    today = timezone.now().date()

    try:
        employee = user.employee_profile
    except Exception:
        employee = None

    # Route to role-specific dashboards
    if user.has_role('super_admin', 'hr_admin', 'hr_executive', 'payroll_admin', 'auditor', 'finance'):
        return hr_dashboard(request, employee, today)
    elif user.is_manager:
        return manager_dashboard(request, employee, today)
    elif employee:
        return employee_dashboard_view(request, employee, today)
    else:
        # No employee profile yet - show generic dashboard
        context = {
            'user': user,
            'employee': employee,
            'today': today,
        }
        return render(request, 'dashboard/modern_dashboard.html', context)


def employee_dashboard_view(request, employee, today):
    # Today's attendance
    today_attendance = Attendance.objects.filter(employee=employee, date=today).first()
    if today_attendance is None and today.weekday() < 5:
        today_attendance = type('MissingAttendance', (), {
            'status': 'absent',
            'clock_in': None,
            'clock_out': None,
            'get_status_display': lambda self: 'Absent',
        })()

    # Monthly stats
    month_start = today.replace(day=1)
    monthly_records = Attendance.objects.filter(
        employee=employee, date__gte=month_start, date__lte=today
    )

    monthly_stats = {
        'present': monthly_records.filter(status__in=['present', 'late_mark']).count(),
        # Do not infer absence from a missing row. An employee may be new,
        # on an unrecorded holiday, or awaiting an admin attendance decision.
        'absent': monthly_records.filter(status='absent').count(),
        'half_day': monthly_records.filter(status='half_day').count(),
        'late_mark': monthly_records.filter(status='late_mark').count(),
        'on_duty': monthly_records.filter(status='on_duty').count(),
    }

    total_mins = sum(r.effective_working_minutes for r in monthly_records)
    monthly_stats['total_hours'] = f"{total_mins // 60}h {total_mins % 60}m"

    # Leave balances
    current_year = today.year
    leave_balances = LeaveBalance.objects.filter(
        employee=employee, year=current_year
    ).select_related('leave_type')[:6]

    leave_available = sum(b.available_days for b in leave_balances)

    # Upcoming holidays
    upcoming_holidays = HolidayCalendar.objects.filter(
        date__gte=today,
        date__lte=today + timedelta(days=30),
        is_active=True
    ).order_by('date')[:5]

    # Pending leave applications
    pending_applications = LeaveApplication.objects.filter(
        employee=employee, status='pending'
    ).select_related('leave_type').order_by('-created_at')[:5]

    # Build calendar data
    cal = calendar.monthcalendar(today.year, today.month)
    month_attendance = {
        r.date: r for r in Attendance.objects.filter(
            employee=employee,
            date__year=today.year,
            date__month=today.month
        )
    }

    # Holiday dates
    holiday_dates = set(HolidayCalendar.objects.filter(
        date__year=today.year,
        date__month=today.month
    ).values_list('date', flat=True))

    calendar_days = []
    # First day offset (calendar.monthcalendar returns Monday=0)
    for week in cal:
        for day_num in week:
            if day_num == 0:
                calendar_days.append({'empty': True})
            else:
                day_date = today.replace(day=day_num)
                record = month_attendance.get(day_date)
                is_today = (day_date == today)
                is_future = day_date > today

                if is_future:
                    css = ''
                elif day_date in holiday_dates:
                    css = 'holiday'
                elif record:
                    status_css_map = {
                        'present': 'present', 'late_mark': 'present',
                        'absent': 'absent', 'half_day': 'half-day',
                        'leave': 'leave', 'on_duty': 'present',
                        'holiday': 'holiday', 'week_off': 'week-off',
                        'work_from_home': 'present',
                    }
                    css = status_css_map.get(record.status, '')
                else:
                    # Check if it's a weekday
                    if day_date.weekday() >= 5:  # Weekend
                        css = 'week-off'
                    elif record and record.status == 'absent':
                        css = 'absent'
                    else:
                        css = ''

                calendar_days.append({
                    'empty': False,
                    'day': day_num,
                    'date': day_date,
                    'is_today': is_today,
                    'css_class': css,
                    'status_display': record.get_status_display() if record else ('Holiday' if day_date in holiday_dates else 'No Record'),
                })

    context = {
        'employee': employee,
        'today': today,
        'greeting': get_greeting(),
        'today_attendance': today_attendance,
        'monthly_stats': monthly_stats,
        'leave_balances': leave_balances,
        'leave_available': int(leave_available),
        'upcoming_holidays': upcoming_holidays,
        'pending_applications': pending_applications,
        'calendar_days': calendar_days,
    }
    return render(request, 'dashboard/employee_dashboard.html', context)


def hr_dashboard(request, employee, today):
    # HR-level stats
    active_employees = Employee.objects.filter(status='active')
    total_employees = active_employees.count()
    approved_today = Attendance.objects.filter(
        employee__status='active', date=today, approval_status='approved'
    )
    today_present = approved_today.filter(
        status__in=['present', 'late_mark', 'on_duty']
    ).values('employee_id').distinct().count()
    # Missing attendance is absent for reporting, without creating a row.
    today_absent = total_employees - approved_today.values('employee_id').distinct().count()
    pending_leaves = LeaveApplication.objects.filter(status='pending').count()

    # Department breakdown
    departments = Department.objects.filter(is_active=True).order_by('name')[:8]
    dept_labels = []
    dept_data = []
    for dept in departments:
        count = dept.employees.filter(status='active').count()
        if count > 0:
            dept_labels.append(dept.name)
            dept_data.append(count)

    # Monthly attendance trend (last 7 days) - single query
    from django.db.models import Count, Q
    period_start = today - timedelta(days=6)
    from django.db.models.functions import TruncDate
    daily_qs = (
        Attendance.objects.filter(date__gte=period_start, date__lte=today, approval_status='approved')
        .annotate(day=TruncDate('date'))
        .values('day')
        .annotate(
            present=Count('employee_id', filter=Q(status__in=['present', 'late_mark', 'on_duty']), distinct=True),
            attended=Count('employee_id', distinct=True),
        )
    )
    daily_map = {str(r['day']): r for r in daily_qs}
    trend_labels = []
    trend_present = []
    trend_absent = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        key = str(day)
        trend_labels.append(day.strftime('%d %b'))
        rec = daily_map.get(key, {})
        trend_present.append(rec.get('present', 0))
        trend_absent.append(max(0, total_employees - rec.get('attended', 0)))

    context = {
        'employee': employee,
        'today': today,
        'greeting': get_greeting(),
        'total_employees': total_employees,
        'today_present': today_present,
        'today_absent': today_absent,
        'pending_leaves': pending_leaves,
        'dept_labels': json.dumps(dept_labels),
        'dept_data': json.dumps(dept_data),
        'trend_labels': json.dumps(trend_labels),
        'trend_present': json.dumps(trend_present),
        'trend_absent': json.dumps(trend_absent),
        'attendance_rate': round((today_present / total_employees * 100) if total_employees else 0, 1),
    }
    return render(request, 'dashboard/hr_dashboard.html', context)


def manager_dashboard(request, employee, today):
    # Get team members
    team = Employee.objects.filter(reporting_manager=employee, status='active')
    team_ids = team.values_list('id', flat=True)

    approved_team_today = Attendance.objects.filter(
        date=today, employee_id__in=team_ids, approval_status='approved'
    )
    team_present = approved_team_today.filter(
        status__in=['present', 'late_mark', 'on_duty']
    ).values('employee_id').distinct().count()
    team_absent = team.count() - approved_team_today.values('employee_id').distinct().count()
    pending_leaves = LeaveApplication.objects.filter(
        employee__in=team, status='pending'
    ).select_related('employee', 'leave_type').order_by('-created_at')[:5]

    context = {
        'employee': employee,
        'today': today,
        'greeting': get_greeting(),
        'team': team,
        'team_count': team.count(),
        'team_present': team_present,
        'team_absent': team_absent,
        'pending_leaves': pending_leaves,
    }
    return render(request, 'dashboard/manager_dashboard.html', context)
