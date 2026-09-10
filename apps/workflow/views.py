from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.attendance.models import Attendance
from apps.employees.models import Employee
from apps.workflow.models import ApprovalAssignment, ApprovalModule, ApprovalRule, SwipeRequest


class SwipeRequestAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if getattr(user, 'is_employee_portal', False):
            try:
                employee = user.employee_profile
            except Exception:
                return Response([])
            qs = SwipeRequest.objects.filter(employee=employee).select_related('attendance').order_by('-created_at')
        else:
            if not getattr(user, 'can_approve_leaves', False):
                return Response({'error': 'Permission denied'}, status=403)
            qs = SwipeRequest.objects.select_related('employee', 'attendance').order_by('-created_at')
        data = []
        for item in qs[:100]:
            data.append({
                'id': str(item.id),
                'employee_id': str(item.employee.id),
                'employee_name': item.employee.get_full_name(),
                'attendance_date': item.attendance.date.isoformat() if item.attendance else None,
                'request_type': item.request_type,
                'requested_in': item.requested_in.isoformat() if item.requested_in else None,
                'requested_out': item.requested_out.isoformat() if item.requested_out else None,
                'reason': item.reason,
                'status': item.status,
                'current_level': item.current_level,
                'reviewer_remarks': item.reviewer_remarks,
                'created_at': item.created_at.isoformat(),
            })
        return Response(data)

    def post(self, request):
        if not getattr(request.user, 'is_employee_portal', False):
            return Response({'error': 'Permission denied'}, status=403)
        try:
            employee = request.user.employee_profile
        except Exception:
            return Response({'error': 'Employee profile not found'}, status=400)

        request_type = request.data.get('request_type')
        attendance_date = request.data.get('attendance_date')
        reason = request.data.get('reason', '').strip()
        if request_type not in ('in', 'out', 'both'):
            return Response({'error': 'Invalid request_type'}, status=400)
        if not attendance_date or not reason:
            return Response({'error': 'attendance_date and reason are required'}, status=400)

        from datetime import datetime
        try:
            d = datetime.fromisoformat(attendance_date).date()
        except ValueError:
            return Response({'error': 'Invalid attendance_date format'}, status=400)

        attendance, _ = Attendance.objects.get_or_create(
            employee=employee,
            date=d,
            defaults={'status': 'absent', 'approval_status': 'pending'}
        )

        if request_type == 'in':
            requested_in = request.data.get('requested_in') or timezone.now()
            requested_out = None
        elif request_type == 'out':
            requested_in = None
            requested_out = request.data.get('requested_out') or timezone.now()
        else:
            requested_in = request.data.get('requested_in') or timezone.now()
            requested_out = request.data.get('requested_out') or timezone.now()

        swipe_request = SwipeRequest.objects.create(
            employee=employee,
            attendance=attendance,
            request_type=request_type,
            requested_in=requested_in,
            requested_out=requested_out,
            reason=reason,
            status='pending',
            current_level=1,
        )

        module = ApprovalModule.objects.filter(name='swipe_request').first()
        if module:
            rule = ApprovalRule.objects.filter(module=module, level_number=1, is_active=True).first()
            if rule:
                assignment = ApprovalAssignment.objects.filter(module=module, rule=rule, is_active=True).first()
                if assignment:
                    swipe_request.current_approver = assignment.user or (assignment.employee.user if assignment.employee else None)
                    swipe_request.save(update_fields=['current_approver'])

        return Response({
            'success': True,
            'message': 'Swipe request submitted for approval',
            'id': str(swipe_request.id),
            'status': swipe_request.status,
        }, status=201)


class SwipeRequestDecisionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            swipe_request = SwipeRequest.objects.get(id=pk)
        except SwipeRequest.DoesNotExist:
            return Response({'error': 'Swipe request not found'}, status=404)

        decision = request.data.get('decision')
        remarks = request.data.get('remarks', '')
        if decision not in ('approved', 'rejected'):
            return Response({'error': "decision must be 'approved' or 'rejected'"}, status=400)

        if decision == 'approved':
            swipe_request.approve(request.user)
        else:
            swipe_request.reject(request.user, remarks)

        return Response({
            'success': True,
            'status': swipe_request.status,
            'decision': decision,
            'remarks': remarks,
        })
