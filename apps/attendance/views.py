"""
WorkSphere HR - Attendance API Views
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta
import math

from apps.attendance.models import (
    Attendance, AttendanceRegularization, ODApplication, ShortTimeOff, SwipeLog
)
from apps.employees.models import Employee


@extend_schema(request=None, responses=None)
class ClockInView(APIView):
    """Mobile and Web clock-in with GPS and selfie"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not getattr(request.user, 'is_employee_portal', False):
            return Response({'error': 'Permission denied for clock-in'}, status=403)

        try:
            employee = request.user.employee_profile
        except Exception:
            return Response({'error': 'Employee profile not found'}, status=400)

        today = timezone.now().date()
        now = timezone.now()

        # Check if already clocked in today
        attendance, created = Attendance.objects.get_or_create(
            employee=employee,
            date=today,
            defaults={'status': 'present', 'approval_status': 'pending'}
        )

        if attendance.clock_in and not created:
            return Response({'error': 'Already clocked in for today'}, status=400)

        # Extract location data
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        address = request.data.get('address', '')
        source = request.data.get('source', 'mobile')

        # Geo-fence validation
        within_geofence = None
        if latitude and longitude and employee.location:
            within_geofence = self._check_geofence(
                float(latitude), float(longitude),
                employee.location
            )

        # Update attendance
        attendance.clock_in = now
        attendance.clock_in_source = source
        attendance.clock_in_latitude = latitude
        attendance.clock_in_longitude = longitude
        attendance.clock_in_address = address
        attendance.clock_in_within_geofence = within_geofence
        attendance.status = 'absent'
        # Every fresh punch needs admin/manager approval before it
        # counts toward attendance reports.
        attendance.approval_status = 'pending'
        attendance.approved_by = None
        attendance.approved_at = None

        # Handle selfie upload (file upload or base64)
        if 'selfie' in request.FILES:
            attendance.clock_in_selfie = request.FILES['selfie']
        elif request.data.get('photo'):
            import base64, io
            from django.core.files.base import ContentFile
            try:
                photo_b64 = request.data['photo']
                photo_bytes = base64.b64decode(photo_b64)
                from django.utils import timezone as tz
                fname = f"clockin_{employee.employee_code}_{tz.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                attendance.clock_in_selfie.save(fname, ContentFile(photo_bytes), save=False)
            except Exception as e:
                pass  # Photo optional — don't fail clock-in

        # Calculate late minutes
        if employee.shift_assignments.filter(is_active=True).exists():
            shift = employee.shift_assignments.filter(is_active=True).first().shift
            shift_start = datetime.combine(today, shift.start_time)
            shift_start = timezone.make_aware(shift_start)
            grace = timezone.timedelta(minutes=shift.grace_period_minutes)

            if now > (shift_start + grace):
                late_mins = int((now - shift_start).total_seconds() / 60)
                attendance.late_minutes = max(0, late_mins - shift.grace_period_minutes)
                if attendance.late_minutes > 0:
                    attendance.status = 'late_mark'

        attendance.save()

        # Create swipe log
        SwipeLog.objects.create(
            employee=employee,
            swipe_time=now,
            swipe_type='in',
            source=source,
            latitude=latitude,
            longitude=longitude,
            is_processed=True,
        )

        return Response({
            'success': True,
            'message': 'Clocked in successfully — pending approval',
            'clock_in': attendance.clock_in.isoformat(),
            'within_geofence': within_geofence,
            'late_minutes': attendance.late_minutes,
            'status': attendance.status,
            'approval_status': attendance.approval_status,
        })

    def _check_geofence(self, lat, lon, location):
        if not location.latitude or not location.longitude:
            return None

        # Haversine formula
        R = 6371000  # Earth's radius in meters
        lat1 = math.radians(float(location.latitude))
        lat2 = math.radians(lat)
        delta_lat = math.radians(lat - float(location.latitude))
        delta_lon = math.radians(lon - float(location.longitude))

        a = (math.sin(delta_lat/2) ** 2 +
             math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon/2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c

        return distance <= location.geo_fence_radius


@extend_schema(request=None, responses=None)
class ClockOutView(APIView):
    """Clock out with GPS"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not getattr(request.user, 'is_employee_portal', False):
            return Response({'error': 'Permission denied for clock-out'}, status=403)

        try:
            employee = request.user.employee_profile
        except Exception:
            return Response({'error': 'Employee profile not found'}, status=400)

        today = timezone.now().date()
        now = timezone.now()

        try:
            attendance = Attendance.objects.get(employee=employee, date=today)
        except Attendance.DoesNotExist:
            return Response({'error': 'No attendance record found for today'}, status=400)

        if not attendance.clock_in:
            return Response({'error': 'You have not clocked in yet'}, status=400)

        if attendance.clock_out:
            return Response({'error': 'Already clocked out for today'}, status=400)

        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        address = request.data.get('address', '')
        source = request.data.get('source', 'mobile')

        within_geofence = None
        if latitude and longitude and employee.location:
            within_geofence = ClockInView()._check_geofence(
                float(latitude), float(longitude), employee.location
            )

        attendance.clock_out = now
        attendance.clock_out_source = source
        attendance.clock_out_latitude = latitude
        attendance.clock_out_longitude = longitude
        attendance.clock_out_address = address
        attendance.clock_out_within_geofence = within_geofence

        if 'selfie' in request.FILES:
            attendance.clock_out_selfie = request.FILES['selfie']
        elif request.data.get('photo'):
            import base64
            from django.core.files.base import ContentFile
            try:
                photo_bytes = base64.b64decode(request.data['photo'])
                fname = f"clockout_{employee.employee_code}_{now.strftime('%Y%m%d_%H%M%S')}.jpg"
                attendance.clock_out_selfie.save(fname, ContentFile(photo_bytes), save=False)
            except Exception:
                pass  # Photo optional — don't fail clock-out

        # Clock-out is a fresh punch too — re-queue for approval so the
        # approver reviews the completed day (in + out + final hours).
        attendance.approval_status = 'pending'
        attendance.approved_by = None
        attendance.approved_at = None
        attendance.status = 'absent'

        # Calculate working hours
        total_mins = int((now - attendance.clock_in).total_seconds() / 60)
        attendance.total_working_minutes = total_mins
        attendance.effective_working_minutes = total_mins - attendance.total_break_minutes

        # Check if half day
        if employee.shift_assignments.filter(is_active=True).exists():
            shift = employee.shift_assignments.filter(is_active=True).first().shift
            half_day_mins = float(shift.minimum_hours) * 60
            full_day_mins = float(shift.full_day_hours) * 60
            if attendance.effective_working_minutes < half_day_mins:
                attendance.status = 'absent'
            elif attendance.effective_working_minutes < full_day_mins:
                attendance.status = 'half_day'

            # Calculate overtime
            if attendance.effective_working_minutes > full_day_mins:
                attendance.overtime_minutes = attendance.effective_working_minutes - int(full_day_mins)

        attendance.save()

        SwipeLog.objects.create(
            employee=employee,
            swipe_time=now,
            swipe_type='out',
            source=source,
            latitude=latitude,
            longitude=longitude,
            is_processed=True,
        )

        return Response({
            'success': True,
            'message': 'Clocked out successfully — pending approval',
            'clock_out': attendance.clock_out.isoformat(),
            'working_hours': attendance.working_hours_display,
            'total_working_minutes': attendance.total_working_minutes,
            'overtime_minutes': attendance.overtime_minutes,
            'approval_status': attendance.approval_status,
        })


@extend_schema(request=None, responses=None)
class BreakInView(APIView):
    """Begin a break during the workday."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not getattr(request.user, 'is_employee_portal', False):
            return Response({'error': 'Permission denied for break-in'}, status=403)

        try:
            employee = request.user.employee_profile
        except Exception:
            return Response({'error': 'Employee profile not found'}, status=400)

        today = timezone.now().date()
        now = timezone.now()

        try:
            attendance = Attendance.objects.get(employee=employee, date=today)
        except Attendance.DoesNotExist:
            return Response({'error': 'No attendance record found for today'}, status=400)

        if attendance.break_in and not attendance.break_out:
            return Response({'error': 'Break already started'}, status=400)
        if attendance.break_out and attendance.clock_out:
            return Response({'error': 'Workday has already ended'}, status=400)

        attendance.break_in = now
        attendance.break_out = None
        attendance.save(update_fields=['break_in', 'break_out'])

        SwipeLog.objects.create(
            employee=employee,
            swipe_time=now,
            swipe_type='break_in',
            source=request.data.get('source', 'web'),
            latitude=request.data.get('latitude'),
            longitude=request.data.get('longitude'),
            is_processed=True,
        )

        return Response({'success': True, 'message': 'Break started', 'break_in': attendance.break_in.isoformat()})


@extend_schema(request=None, responses=None)
class BreakOutView(APIView):
    """End a break and update the current attendance record."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not getattr(request.user, 'is_employee_portal', False):
            return Response({'error': 'Permission denied for break-out'}, status=403)

        try:
            employee = request.user.employee_profile
        except Exception:
            return Response({'error': 'Employee profile not found'}, status=400)

        today = timezone.now().date()
        now = timezone.now()

        try:
            attendance = Attendance.objects.get(employee=employee, date=today)
        except Attendance.DoesNotExist:
            return Response({'error': 'No attendance record found for today'}, status=400)

        if not attendance.break_in:
            return Response({'error': 'Break has not been started'}, status=400)
        if attendance.break_out:
            return Response({'error': 'Break already ended'}, status=400)

        attendance.break_out = now
        break_minutes = int((attendance.break_out - attendance.break_in).total_seconds() / 60)
        attendance.total_break_minutes = (attendance.total_break_minutes or 0) + max(0, break_minutes)

        if attendance.clock_in and attendance.clock_out:
            total_mins = int((attendance.clock_out - attendance.clock_in).total_seconds() / 60)
            attendance.total_working_minutes = total_mins
            attendance.effective_working_minutes = max(0, total_mins - attendance.total_break_minutes)

        attendance.save(update_fields=['break_out', 'total_break_minutes', 'effective_working_minutes', 'total_working_minutes'])

        SwipeLog.objects.create(
            employee=employee,
            swipe_time=now,
            swipe_type='break_out',
            source=request.data.get('source', 'web'),
            latitude=request.data.get('latitude'),
            longitude=request.data.get('longitude'),
            is_processed=True,
        )

        return Response({
            'success': True,
            'message': 'Break ended',
            'break_out': attendance.break_out.isoformat(),
            'break_duration_minutes': break_minutes,
            'total_break_minutes': attendance.total_break_minutes,
        })


class AttendanceViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    # Provide a default queryset and serializer for schema generation
    queryset = Attendance.objects.none()
    from apps.attendance.serializers import AttendanceSerializer
    serializer_class = AttendanceSerializer

    def get_queryset(self):
        user = self.request.user
        # Swagger/schema generation and anonymous requests should return empty queryset
        if not getattr(user, 'is_authenticated', False):
            return Attendance.objects.none()
        qs = Attendance.objects.select_related('employee', 'shift')

        if user.is_employee:
            try:
                # Employees always see their own full history (including
                # pending/rejected) — they need to track their own status.
                qs = qs.filter(employee=user.employee_profile)
            except Exception:
                return Attendance.objects.none()
        elif user.is_manager or user.is_reporting_manager or user.is_project_manager:
            try:
                manager_emp = user.employee_profile
                team_ids = Employee.objects.filter(
                    reporting_manager=manager_emp
                ).values_list('id', flat=True)
                qs = qs.filter(employee_id__in=team_ids)
                # Managers/HR/admin viewing OTHER people's attendance only
                # ever see approved punches — pending/rejected stay hidden
                # until an approver acts on them.
                if self.request.query_params.get('include_pending') != 'true':
                    qs = qs.filter(approval_status='approved')
            except Exception:
                return Attendance.objects.none()
        elif user.has_role('super_admin', 'hr_admin', 'hr_executive', 'finance', 'payroll_admin', 'auditor'):
            if self.request.query_params.get('include_pending') != 'true':
                qs = qs.filter(approval_status='approved')
        else:
            return Attendance.objects.none()

        # Date filters
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        employee_id = self.request.query_params.get('employee_id')
        status_filter = self.request.query_params.get('status')

        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)
        if employee_id:
            qs = qs.filter(employee_id=employee_id)
        if status_filter:
            qs = qs.filter(status=status_filter)

        return qs.order_by('-date')

    def get_serializer_class(self):
        from apps.attendance.serializers import AttendanceSerializer
        return AttendanceSerializer

    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's attendance for current user"""
        try:
            employee = request.user.employee_profile
            today = timezone.now().date()
            attendance = Attendance.objects.filter(employee=employee, date=today).first()
            if attendance:
                from apps.attendance.serializers import AttendanceSerializer
                return Response(AttendanceSerializer(attendance).data)
            return Response({'date': str(today), 'status': 'not_marked', 'clock_in': None, 'clock_out': None})
        except Exception:
            return Response({'error': 'Profile not found'}, status=400)

    @action(detail=False, methods=['get'])
    def monthly_summary(self, request):
        """Monthly attendance summary"""
        try:
            employee = request.user.employee_profile
        except Exception:
            return Response({'error': 'Profile not found'}, status=400)

        year = int(request.query_params.get('year', timezone.now().year))
        month = int(request.query_params.get('month', timezone.now().month))

        records = Attendance.objects.filter(
            employee=employee,
            date__year=year,
            date__month=month
        )

        from collections import Counter
        status_counts = Counter(records.values_list('status', flat=True))

        from django.db.models import Sum
        agg = records.aggregate(tw=Sum('effective_working_minutes'), ot=Sum('overtime_minutes'))
        total_working_mins = agg['tw'] or 0
        total_overtime_mins = agg['ot'] or 0

        return Response({
            'year': year,
            'month': month,
            'total_days': records.count(),
            'present': status_counts.get('present', 0),
            'absent': status_counts.get('absent', 0),
            'half_day': status_counts.get('half_day', 0),
            'late_mark': status_counts.get('late_mark', 0),
            'on_duty': status_counts.get('on_duty', 0),
            'work_from_home': status_counts.get('work_from_home', 0),
            'leave': status_counts.get('leave', 0),
            'holiday': status_counts.get('holiday', 0),
            'total_working_hours': f"{total_working_mins // 60}h {total_working_mins % 60}m",
            'total_overtime_hours': f"{total_overtime_mins // 60}h {total_overtime_mins % 60}m",
            'total_overtime_minutes': total_overtime_mins,
        })

    @action(detail=False, methods=['get'])
    def pending_approvals(self, request):
        """List punches awaiting approval — for managers/HR/admin."""
        user = request.user
        if not (user.is_manager or user.is_reporting_manager or user.is_project_manager
                or user.has_role('super_admin', 'hr_admin', 'hr_executive', 'auditor')):
            return Response({'error': 'Permission denied'}, status=403)

        qs = Attendance.objects.filter(approval_status='pending').select_related('employee', 'employee__department')

        if not user.has_role('super_admin', 'hr_admin', 'hr_executive', 'auditor'):
            try:
                manager_emp = user.employee_profile
                team_ids = Employee.objects.filter(reporting_manager=manager_emp).values_list('id', flat=True)
                qs = qs.filter(employee_id__in=team_ids)
            except Exception:
                return Response([])

        qs = qs.order_by('-date', '-clock_in')[:200]
        data = [{
            'id': str(a.id),
            'employee_id': str(a.employee.id),
            'employee_name': a.employee.get_full_name(),
            'employee_code': a.employee.employee_code,
            'department': a.employee.department.name if a.employee.department else None,
            'date': a.date.isoformat(),
            'clock_in': a.clock_in.isoformat() if a.clock_in else None,
            'clock_out': a.clock_out.isoformat() if a.clock_out else None,
            'effective_working_minutes': a.effective_working_minutes,
            'status': a.status,
            'clock_in_within_geofence': a.clock_in_within_geofence,
            'clock_out_within_geofence': a.clock_out_within_geofence,
            'clock_in_latitude': str(a.clock_in_latitude) if a.clock_in_latitude is not None else None,
            'clock_in_longitude': str(a.clock_in_longitude) if a.clock_in_longitude is not None else None,
            'has_clock_in_photo': bool(a.clock_in_selfie),
            'has_clock_out_photo': bool(a.clock_out_selfie),
            'clock_in_photo_url': a.clock_in_selfie.url if a.clock_in_selfie else None,
            'clock_out_photo_url': a.clock_out_selfie.url if a.clock_out_selfie else None,
        } for a in qs]
        return Response(data)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve or reject a single attendance punch."""
        user = request.user
        if not (user.is_manager or user.is_reporting_manager or user.is_project_manager
                or user.has_role('super_admin', 'hr_admin', 'hr_executive', 'auditor')):
            return Response({'error': 'Permission denied'}, status=403)

        try:
            attendance = Attendance.objects.select_related('employee').get(id=pk)
        except Attendance.DoesNotExist:
            return Response({'error': 'Attendance record not found'}, status=404)

        # Managers can only act on their own team's punches
        if not user.has_role('super_admin', 'hr_admin', 'hr_executive', 'auditor'):
            try:
                manager_emp = user.employee_profile
                if attendance.employee.reporting_manager_id != manager_emp.id:
                    return Response({'error': 'You can only approve your own team\u2019s attendance'}, status=403)
            except Exception:
                return Response({'error': 'Permission denied'}, status=403)

        decision = request.data.get('decision')
        if decision not in ('approved', 'rejected'):
            return Response({'error': "decision must be 'approved' or 'rejected'"}, status=400)

        attendance.approval_status = decision
        attendance.approved_by = user
        attendance.approved_at = timezone.now()
        attendance.approval_remarks = request.data.get('remarks', '')

        if decision == 'approved' and attendance.clock_in and attendance.clock_out:
            attendance.status = 'present'

        if decision == 'rejected':
            # A rejected punch should not silently read as a normal absence
            # in reports — mark it explicitly so HR can see it was disputed.
            attendance.admin_remarks = (attendance.admin_remarks + '\n' if attendance.admin_remarks else '') + \
                f"Rejected by {user.email} on {timezone.now().strftime('%Y-%m-%d %H:%M')}: {attendance.approval_remarks}"
        attendance.save(update_fields=['approval_status', 'approved_by', 'approved_at', 'approval_remarks', 'admin_remarks'])

        from apps.attendance.serializers import AttendanceSerializer
        return Response({
            'success': True,
            'message': f'Attendance {decision}',
            'data': AttendanceSerializer(attendance).data,
        })
