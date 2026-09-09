"""WorkSphere HR - Payroll API Views"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.http import HttpResponse
from django.utils import timezone
from drf_spectacular.utils import extend_schema

from .models import PayslipRecord, PayrollPeriod


def serialize_payslip(ps, detail=False):
    period = ps.payroll_period
    base = {
        'id': str(ps.id),
        'payslip_number': ps.payslip_number,
        'period': {'year': period.year, 'month': period.month, 'month_name': period.get_month_display() if hasattr(period, 'get_month_display') else str(period.month)},
        'gross_earnings': float(ps.gross_earnings),
        'total_deductions': float(ps.total_deductions),
        'net_salary': float(ps.net_salary),
        'days_present': float(ps.days_present),
        'days_absent': float(ps.days_absent),
        'status': ps.status,
        'payment_date': ps.payment_date.isoformat() if ps.payment_date else None,
        'has_pdf': bool(ps.payslip_pdf),
    }
    if detail:
        base.update({
            'basic': float(ps.basic),
            'hra': float(ps.hra),
            'special_allowance': float(ps.special_allowance),
            'medical_allowance': float(ps.medical_allowance),
            'conveyance_allowance': float(ps.conveyance_allowance),
            'bonus': float(ps.bonus),
            'overtime_amount': float(ps.overtime_amount),
            'pf_employee': float(ps.pf_employee),
            'esi_employee': float(ps.esi_employee),
            'professional_tax': float(ps.professional_tax),
            'tds': float(ps.tds),
            'loan_deduction': float(ps.loan_deduction),
            'other_deductions': float(ps.other_deductions),
            'calculation_details': ps.calculation_details,
        })
    return base


@extend_schema(request=None, responses=None)
class MyPayslipsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            emp = request.user.employee_profile
        except Exception:
            return Response([])
        year = request.query_params.get('year')
        qs = PayslipRecord.objects.filter(
            employee=emp, status__in=('released', 'paid')
        ).select_related('payroll_period').order_by('-payroll_period__year', '-payroll_period__month')
        if year:
            qs = qs.filter(payroll_period__year=int(year))
        return Response([serialize_payslip(ps) for ps in qs[:24]])


@extend_schema(request=None, responses=None)
class PayslipDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            ps = PayslipRecord.objects.select_related('payroll_period', 'employee').get(id=pk)
        except PayslipRecord.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
        if not request.user.is_admin_portal:
            try:
                if ps.employee != request.user.employee_profile:
                    return Response({'error': 'Permission denied'}, status=403)
            except Exception:
                return Response({'error': 'Permission denied'}, status=403)
            if ps.status not in ('released', 'paid'):
                return Response({'error': 'This payslip has not been released.'}, status=403)
        return Response(serialize_payslip(ps, detail=True))


@extend_schema(request=None, responses=None)
class PayslipPDFAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            payslip = PayslipRecord.objects.select_related(
                'payroll_period', 'employee', 'employee__department', 'employee__designation'
            ).get(pk=pk)
        except PayslipRecord.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        is_payroll_user = getattr(request.user, 'can_manage_payroll', False)
        is_owner = False
        if not is_payroll_user:
            try:
                is_owner = payslip.employee == request.user.employee_profile
            except Exception:
                is_owner = False
            if not is_owner or payslip.status not in ('released', 'paid'):
                return Response({'error': 'This payslip is not available.'}, status=403)
        if payslip.status == 'draft':
            return Response({'error': 'Draft payslips cannot be downloaded.'}, status=409)

        from .pdf_service import generate_payslip_pdf
        content = generate_payslip_pdf(payslip)
        response = HttpResponse(content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{payslip.payslip_number}.pdf"'
        return response


@extend_schema(request=None, responses=None)
class PayrollSummaryAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not getattr(request.user, 'can_manage_payroll', False):
            return Response({'error': 'Permission denied'}, status=403)
        today = timezone.now()
        from django.db.models import Sum, Count
        periods = PayrollPeriod.objects.order_by('-year', '-month')[:12]
        return Response([{
            'year': p.year,
            'month': p.month,
            'total_payslips': p.payslips.count(),
            'total_net': float(p.payslips.aggregate(s=Sum('net_salary'))['s'] or 0),
            'status': p.status,
        } for p in periods])
