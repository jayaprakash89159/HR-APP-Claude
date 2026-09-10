"""WorkSphere HR - Leave Management API Views"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Q
from drf_spectacular.utils import extend_schema

from .models import LeaveType, LeaveBalance, LeaveApplication, HolidayCalendar
from apps.employees.models import Employee


class LeaveTypeSerializer:
    """Inline serializer"""
    @staticmethod
    def serialize(lt):
        return {
            'id': str(lt.id), 'name': lt.name, 'code': lt.code,
            'category': lt.category, 'days_allowed_per_year': float(lt.days_allowed_per_year),
            'allow_half_day': lt.allow_half_day, 'is_paid': lt.is_paid,
            'requires_document': lt.requires_document, 'color': lt.color,
        }


class LeaveBalanceSerializer:
    @staticmethod
    def serialize(b):
        return {
            'id': str(b.id), 'leave_type': LeaveTypeSerializer.serialize(b.leave_type),
            'year': b.year, 'entitled_days': float(b.entitled_days),
            'carried_forward': float(b.carried_forward), 'accrued': float(b.accrued),
            'availed': float(b.availed), 'lapsed': float(b.lapsed),
            'encashed': float(b.encashed), 'available_days': float(b.available_days),
        }


class LeaveApplicationSerializer:
    @staticmethod
    def serialize(app):
        return {
            'id': str(app.id), 'application_number': app.application_number,
            'leave_type': LeaveTypeSerializer.serialize(app.leave_type),
            'from_date': app.from_date.isoformat(), 'to_date': app.to_date.isoformat(),
            'total_days': float(app.total_days), 'reason': app.reason,
            'status': app.status, 'status_display': app.get_status_display(),
            'created_at': app.created_at.isoformat(),
            'number_of_days': float(app.total_days),
        }


@extend_schema(request=None, responses=None)
class LeaveTypesAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        types = LeaveType.objects.filter(is_active=True).order_by('name')
        return Response([LeaveTypeSerializer.serialize(lt) for lt in types])


@extend_schema(request=None, responses=None)
class LeaveBalancesAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            employee = request.user.employee_profile
        except Exception:
            return Response([])
        year = int(request.query_params.get('year', timezone.now().year))
        balances = LeaveBalance.objects.filter(employee=employee, year=year).select_related('leave_type')
        return Response([LeaveBalanceSerializer.serialize(b) for b in balances])


@extend_schema(request=None, responses=None)
class LeaveApplicationsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.is_admin_portal:
            # Admin can see all or filtered
            qs = LeaveApplication.objects.select_related('employee', 'leave_type').order_by('-from_date')
            emp_id = request.query_params.get('employee_id')
            status_filter = request.query_params.get('status')
            if emp_id:
                qs = qs.filter(employee_id=emp_id)
            if status_filter:
                qs = qs.filter(status=status_filter)
        else:
            try:
                employee = user.employee_profile
            except Exception:
                return Response([])
            qs = LeaveApplication.objects.filter(employee=employee).select_related('leave_type').order_by('-from_date')
        return Response([LeaveApplicationSerializer.serialize(a) for a in qs[:100]])

    def post(self, request):
        try:
            employee = request.user.employee_profile
        except Exception:
            return Response({'error': 'Employee profile not found'}, status=400)

        data = request.data
        try:
            lt = LeaveType.objects.get(id=data.get('leave_type_id'))
        except LeaveType.DoesNotExist:
            return Response({'error': 'Invalid leave type'}, status=400)

        from_date = data.get('from_date')
        to_date = data.get('to_date')
        reason = data.get('reason', '').strip()

        if not from_date or not to_date or not reason:
            return Response({'error': 'from_date, to_date, and reason are required'}, status=400)

        from datetime import date
        try:
            fd = date.fromisoformat(str(from_date))
            td = date.fromisoformat(str(to_date))
        except ValueError:
            return Response({'error': 'Invalid date format'}, status=400)

        if fd > td:
            return Response({'error': 'from_date must be before to_date'}, status=400)

        # Calculate business days
        days = (td - fd).days + 1

        app = LeaveApplication.objects.create(
            employee=employee,
            leave_type=lt,
            from_date=fd,
            to_date=td,
            total_days=days,
            reason=reason,
            status='pending',
        )
        return Response(LeaveApplicationSerializer.serialize(app), status=201)


@extend_schema(request=None, responses=None)
class LeaveApplicationDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk, user):
        try:
            app = LeaveApplication.objects.get(id=pk)
        except LeaveApplication.DoesNotExist:
            return None
        if not user.is_admin_portal and app.employee.user != user:
            return None
        return app

    def patch(self, request, pk):
        """Approve/reject a leave application through configured manager/HR stages."""
        if not getattr(request.user, 'can_approve_leaves', False):
            return Response({'error': 'Permission denied'}, status=403)
        app = self.get_object(pk, request.user)
        if not app:
            return Response({'error': 'Not found'}, status=404)

        new_status = request.data.get('status')
        level = int(request.data.get('level', 1))
        remarks = request.data.get('remarks', '')

        if new_status not in ('approved', 'rejected', 'cancelled'):
            return Response({'error': 'Invalid status'}, status=400)

        if new_status == 'approved':
            if level == 1:
                app.manager_status = 'approved'
                app.manager_reviewed_by = request.user
                app.manager_reviewed_at = timezone.now()
                app.manager_remarks = remarks
                app.current_approval_level = 2
                app.status = 'pending'
            elif level == 2:
                app.hr_status = 'approved'
                app.hr_reviewed_by = request.user
                app.hr_reviewed_at = timezone.now()
                app.hr_remarks = remarks
                app.current_approval_level = 2
                if app.manager_status == 'approved':
                    app.status = 'approved'
                else:
                    app.status = 'pending'
            else:
                app.status = 'approved'
        elif new_status == 'rejected':
            if level == 1:
                app.manager_status = 'rejected'
                app.manager_reviewed_by = request.user
                app.manager_reviewed_at = timezone.now()
                app.manager_remarks = remarks
            elif level == 2:
                app.hr_status = 'rejected'
                app.hr_reviewed_by = request.user
                app.hr_reviewed_at = timezone.now()
                app.hr_remarks = remarks
            app.status = 'rejected'
        else:
            app.status = 'cancelled'

        app.save()
        return Response(LeaveApplicationSerializer.serialize(app))


@extend_schema(request=None, responses=None)
class HolidaysAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        year = int(request.query_params.get('year', timezone.now().year))
        holidays = HolidayCalendar.objects.filter(date__year=year, is_active=True).order_by('date')
        data = [{
            'id': str(h.id), 'name': h.name, 'date': h.date.isoformat(),
            'holiday_type': h.holiday_type, 'description': h.description,
        } for h in holidays]
        return Response(data)


@extend_schema(request=None, responses=None)
class LeavePendingApprovalsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not getattr(request.user, 'can_approve_leaves', False):
            return Response({'error': 'Permission denied'}, status=403)
        user = request.user
        if user.is_admin_portal:
            qs = LeaveApplication.objects.filter(status='pending').select_related('employee', 'leave_type', 'employee__department').order_by('-created_at')
        else:
            try:
                manager_emp = user.employee_profile
                team = Employee.objects.filter(reporting_manager=manager_emp)
                qs = LeaveApplication.objects.filter(
                    employee__in=team,
                    status='pending',
                    current_approval_level=1
                ).select_related('employee', 'leave_type').order_by('-created_at')
            except Exception:
                return Response([])
        result = []
        for app in qs[:50]:
            d = LeaveApplicationSerializer.serialize(app)
            d['employee_name'] = app.employee.get_full_name()
            d['department'] = app.employee.department.name if app.employee.department else '—'
            result.append(d)
        return Response(result)
