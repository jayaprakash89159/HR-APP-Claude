from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import EmployeeSalary, PayrollPeriod
from .period_serializers import PayrollPeriodSerializer
from .permissions import CanManagePayroll
from .services import PayrollCalculationError, process_payroll_period


class PayrollPeriodListCreateView(generics.ListCreateAPIView):
    permission_classes = [CanManagePayroll]
    queryset = PayrollPeriod.objects.select_related(
        'processed_by', 'approved_by', 'released_by', 'paid_by', 'locked_by'
    ).all()
    serializer_class = PayrollPeriodSerializer

    def perform_create(self, serializer):
        data = serializer.validated_data
        serializer.save(name=data.get('name') or f"Payroll {data['year']}-{data['month']:02d}")


class PayrollPeriodDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [CanManagePayroll]
    queryset = PayrollPeriod.objects.all()
    serializer_class = PayrollPeriodSerializer


class PayrollPeriodTransitionView(APIView):
    permission_classes = [CanManagePayroll]

    transitions = {
        'process': ('draft', 'processing'),
        'approve': ('processed', 'approved'),
        'release': ('approved', 'released'),
        'mark_paid': ('released', 'paid'),
        'lock': ('paid', 'locked'),
    }

    def post(self, request, pk):
        action = request.data.get('action')
        if action not in self.transitions:
            return Response({'error': 'Unsupported payroll action.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            try:
                period = PayrollPeriod.objects.select_for_update().get(pk=pk)
            except PayrollPeriod.DoesNotExist:
                return Response({'error': 'Payroll period not found.'}, status=status.HTTP_404_NOT_FOUND)

            expected, target = self.transitions[action]
            if period.status != expected:
                return Response(
                    {'error': f'Cannot {action} a period in {period.status} status.'},
                    status=status.HTTP_409_CONFLICT,
                )

            if action == 'process':
                active_employees = PayrollPeriodTransitionView._active_employee_ids()
                configured_employees = set(
                    EmployeeSalary.objects.filter(
                        employee_id__in=active_employees,
                        is_active=True,
                        effective_from__lte=period.to_date,
                    ).filter(
                        Q(effective_to__isnull=True) | Q(effective_to__gte=period.from_date)
                    ).values_list('employee_id', flat=True)
                )
                missing = active_employees - configured_employees
                if missing:
                    return Response(
                        {'error': 'Every active employee needs an effective salary record.', 'missing_employee_ids': [str(employee_id) for employee_id in missing]},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                period.status = 'processing'
                period.save(update_fields=['status'])
                try:
                    period = process_payroll_period(period.pk, request.user)
                except PayrollCalculationError as exc:
                    return Response({'error': str(exc), 'details': exc.details}, status=status.HTTP_400_BAD_REQUEST)

            if action in ('approve', 'release', 'mark_paid', 'lock') and not period.payslips.exists():
                return Response({'error': 'The period has no payslips.'}, status=status.HTTP_400_BAD_REQUEST)

            now = timezone.now()
            period.status = target
            if action == 'approve':
                period.approved_at, period.approved_by = now, request.user
                period.payslips.filter(status='generated').update(status='approved')
            elif action == 'release':
                period.released_at, period.released_by = now, request.user
                period.payslips.filter(status='approved').update(status='released', released_at=now, released_by=request.user)
            elif action == 'mark_paid':
                period.paid_at, period.paid_by = now, request.user
                period.payslips.filter(status__in=('approved', 'released')).update(status='paid')
            elif action == 'lock':
                period.locked_at, period.locked_by = now, request.user
            period.remarks = request.data.get('remarks', period.remarks)
            period.save()

        return Response(PayrollPeriodSerializer(period).data)

    @staticmethod
    def _active_employee_ids():
        from apps.employees.models import Employee
        return set(Employee.objects.filter(status='active').values_list('id', flat=True))
