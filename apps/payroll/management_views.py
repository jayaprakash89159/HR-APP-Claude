from rest_framework import generics

from .models import EmployeeSalary, SalaryComponent, SalaryStructure
from .permissions import CanManagePayroll
from .serializers import EmployeeSalarySerializer, SalaryComponentSerializer, SalaryStructureSerializer


class PayrollManageMixin:
    permission_classes = [CanManagePayroll]


class SalaryComponentListCreateView(PayrollManageMixin, generics.ListCreateAPIView):
    queryset = SalaryComponent.objects.all().order_by('component_type', 'display_order', 'name')
    serializer_class = SalaryComponentSerializer


class SalaryComponentDetailView(PayrollManageMixin, generics.RetrieveUpdateAPIView):
    queryset = SalaryComponent.objects.all()
    serializer_class = SalaryComponentSerializer


class SalaryStructureListCreateView(PayrollManageMixin, generics.ListCreateAPIView):
    queryset = SalaryStructure.objects.prefetch_related('components__component').all().order_by('name')
    serializer_class = SalaryStructureSerializer


class SalaryStructureDetailView(PayrollManageMixin, generics.RetrieveUpdateAPIView):
    queryset = SalaryStructure.objects.prefetch_related('components__component').all()
    serializer_class = SalaryStructureSerializer


class EmployeeSalaryListCreateView(PayrollManageMixin, generics.ListCreateAPIView):
    queryset = EmployeeSalary.objects.select_related('employee', 'salary_structure').all()
    serializer_class = EmployeeSalarySerializer
    filterset_fields = ['employee', 'salary_structure', 'is_active']


class EmployeeSalaryDetailView(PayrollManageMixin, generics.RetrieveUpdateAPIView):
    queryset = EmployeeSalary.objects.select_related('employee', 'salary_structure').all()
    serializer_class = EmployeeSalarySerializer