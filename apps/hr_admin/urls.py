from django.urls import path
from apps.dashboard import hr_views
from . import views

app_name = 'hr_admin'

urlpatterns = [
    path('',                                views.admin_dashboard,            name='admin_dashboard'),
    path('approval-flow/',                  views.approval_flow_dashboard,    name='approval_flow_dashboard'),

    # Payroll management (inside admin portal only)
    path('payroll/',                        views.payroll_management,         name='payroll_management'),
    path('payroll/components/',             views.payroll_components,         name='payroll_components'),
    path('payroll/components/add/',         views.payroll_component_add,      name='payroll_component_add'),
    path('payroll/components/<uuid:pk>/edit/', views.payroll_component_edit,    name='payroll_component_edit'),
    path('payroll/structures/',             views.payroll_structures,         name='payroll_structures'),
    path('payroll/structures/add/',         views.payroll_structure_add,      name='payroll_structure_add'),
    path('payroll/structures/<uuid:pk>/edit/', views.payroll_structure_edit,    name='payroll_structure_edit'),
    path('payroll/employee-salaries/',      views.payroll_employee_salaries,  name='payroll_employee_salaries'),
    path('payroll/employee-salaries/add/', views.payroll_employee_salary_add, name='payroll_employee_salary_add'),
    path('payroll/employee-salaries/<uuid:pk>/edit/', views.payroll_employee_salary_edit, name='payroll_employee_salary_edit'),
    path('payroll/periods/',                views.payroll_periods,            name='payroll_periods'),
    path('payroll/periods/add/',            views.payroll_period_add,         name='payroll_period_add'),
    path('payroll/periods/<uuid:pk>/edit/', views.payroll_period_edit,       name='payroll_period_edit'),

    # Employees
    path('employees/',                      views.employee_list,              name='employee_list'),
    path('employees/add/',                  views.employee_add,               name='employee_add'),
    path('employees/bulk-upload/',          views.employee_bulk_upload_page,  name='employee_bulk_upload_page'),
    path('employees/bulk-upload/process/',  views.employee_bulk_upload,       name='employee_bulk_upload'),
    path('employees/bulk-upload/template/', views.employee_csv_template,      name='employee_csv_template'),
    path('employees/<uuid:pk>/',            views.employee_detail,            name='employee_detail'),
    path('employees/<uuid:pk>/edit/',       views.employee_edit,              name='employee_edit'),

    # Departments
    path('departments/',                    views.department_list,            name='department_list'),
    path('departments/add/',                views.department_add,             name='department_add'),
    path('departments/bulk-upload/',        views.department_bulk_upload,     name='department_bulk_upload'),
    path('departments/template/',           views.department_csv_template,    name='department_csv_template'),
    path('departments/<uuid:pk>/edit/',     views.department_edit,            name='department_edit'),

    # Designations
    path('designations/',                   views.designation_list,           name='designation_list'),
    path('designations/add/',               views.designation_add,            name='designation_add'),
    path('designations/bulk-upload/',       views.designation_bulk_upload,    name='designation_bulk_upload'),
    path('designations/template/',          views.designation_csv_template,   name='designation_csv_template'),
    path('designations/<uuid:pk>/edit/',    views.designation_edit,           name='designation_edit'),

    # Locations
    path('locations/',                      views.location_list,              name='location_list'),
    path('locations/add/',                  views.location_add,               name='location_add'),
    path('locations/bulk-upload/',          views.location_bulk_upload,       name='location_bulk_upload'),
    path('locations/template/',             views.location_csv_template,      name='location_csv_template'),
    path('locations/<uuid:pk>/edit/',       views.location_edit,              name='location_edit'),

    # Users
    path('users/',                          views.user_list,                  name='user_list'),
    path('users/add/',                      views.user_add,                   name='user_add'),
    path('users/<uuid:pk>/edit/',           views.user_edit,                  name='user_edit'),

    # Leave Types
    path('leave-types/',                    views.leave_type_list,            name='leave_type_list'),
    path('leave-types/add/',                views.leave_type_add,             name='leave_type_add'),
    path('leave-types/<uuid:pk>/edit/',     views.leave_type_edit,            name='leave_type_edit'),

    # Attendance
    path('attendance/',                     views.attendance_list,            name='attendance_list'),
    path('attendance/approvals/',           views.attendance_approvals,       name='attendance_approvals'),
    path('attendance/<uuid:pk>/decide/',    views.attendance_approve_action,  name='attendance_approve_action'),
    path('attendance/bulk-upload/',         views.attendance_bulk_upload,     name='attendance_bulk_upload'),
    path('attendance/template/',            views.attendance_csv_template,    name='attendance_csv_template'),

    # Leaves
    path('leaves/',                         views.leave_list,                 name='leave_list'),
    path('leaves/bulk-upload/',             views.leave_bulk_upload,          name='leave_bulk_upload'),
    path('leaves/template/',                views.leave_csv_template,         name='leave_csv_template'),
]
