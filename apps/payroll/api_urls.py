"""WorkSphere HR - Payroll API URLs"""
from django.urls import path
from . import api_views
from . import management_views
from . import period_views

urlpatterns = [
    path('payslips/', api_views.MyPayslipsAPIView.as_view(), name='my_payslips'),
    path('payslips/<uuid:pk>/', api_views.PayslipDetailAPIView.as_view(), name='payslip_detail'),
    path('payslips/<uuid:pk>/pdf/', api_views.PayslipPDFAPIView.as_view(), name='payslip_pdf'),
    path('summary/', api_views.PayrollSummaryAPIView.as_view(), name='payroll_summary'),
    path('manage/components/', management_views.SalaryComponentListCreateView.as_view(), name='manage_salary_components'),
    path('manage/components/<uuid:pk>/', management_views.SalaryComponentDetailView.as_view(), name='manage_salary_component'),
    path('manage/structures/', management_views.SalaryStructureListCreateView.as_view(), name='manage_salary_structures'),
    path('manage/structures/<uuid:pk>/', management_views.SalaryStructureDetailView.as_view(), name='manage_salary_structure'),
    path('manage/employee-salaries/', management_views.EmployeeSalaryListCreateView.as_view(), name='manage_employee_salaries'),
    path('manage/employee-salaries/<uuid:pk>/', management_views.EmployeeSalaryDetailView.as_view(), name='manage_employee_salary'),
    path('manage/periods/', period_views.PayrollPeriodListCreateView.as_view(), name='manage_payroll_periods'),
    path('manage/periods/<uuid:pk>/', period_views.PayrollPeriodDetailView.as_view(), name='manage_payroll_period'),
    path('manage/periods/<uuid:pk>/transition/', period_views.PayrollPeriodTransitionView.as_view(), name='manage_payroll_period_transition'),
]
