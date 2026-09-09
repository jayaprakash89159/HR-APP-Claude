"""
WorkSphere HR - Complete Custom Admin Views
No Django Admin redirects. Everything is a proper custom page.
Author: Senior Dev (20yr)
"""
import csv, io, json, uuid
from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction, IntegrityError
from django.db.models import Q, Count, Sum
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt


# ─────────────────────────────────────────────
# Guard decorator
# ─────────────────────────────────────────────
def admin_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not getattr(request.user, 'is_admin_portal', False):
            raise PermissionDenied("Admin access required.")
        return view_func(request, *args, **kwargs)
    return wrapper


def api_admin_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not getattr(request.user, 'is_admin_portal', False):
            return JsonResponse({'error': 'Admin access required'}, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


# ─────────────────────────────────────────────
# EMPLOYEE MANAGEMENT
# ─────────────────────────────────────────────
@admin_required
def employee_list(request):
    from apps.employees.models import Employee, Department, Designation, Location
    qs = Employee.objects.select_related('department', 'designation', 'location', 'user').order_by('first_name', 'last_name')
    search = request.GET.get('q', '').strip()
    dept_id = request.GET.get('dept', '')
    status_filter = request.GET.get('status', 'active')
    if search:
        qs = qs.filter(Q(first_name__icontains=search) | Q(last_name__icontains=search) |
                       Q(employee_code__icontains=search) | Q(official_email__icontains=search))
    if dept_id:
        qs = qs.filter(department_id=dept_id)
    if status_filter:
        qs = qs.filter(status=status_filter)
    return render(request, 'hr_admin/employees/list.html', {
        'employees': qs[:300],
        'total': qs.count(),
        'departments': Department.objects.filter(is_active=True).order_by('name'),
        'search': search, 'dept_id': dept_id, 'status_filter': status_filter,
    })


@admin_required
def employee_add(request):
    from apps.employees.models import Employee, Department, Designation, Location
    from apps.authentication.models import User
    if request.method == 'POST':
        try:
            with transaction.atomic():
                data = request.POST
                # Create user account
                email = data.get('official_email', '').strip().lower()
                if not email:
                    messages.error(request, 'Official email is required.')
                    raise ValueError('email required')
                if User.objects.filter(email=email).exists():
                    messages.error(request, f'User with email {email} already exists.')
                    raise ValueError('email exists')

                user = User.objects.create_user(
                    email=email,
                    password='Welcome@123',  # temp password
                    role='employee',
                )

                dept = Department.objects.get(id=data['department'])
                desig = Designation.objects.get(id=data['designation'])
                loc = Location.objects.get(id=data['location'])

                # Auto-generate employee_code
                last = Employee.objects.order_by('-created_at').first()
                next_num = 1001
                if last and last.employee_code:
                    try:
                        next_num = int(last.employee_code.replace('EMP','')) + 1
                    except:
                        pass
                emp_code = f'EMP{next_num:04d}'

                emp = Employee.objects.create(
                    user=user,
                    employee_id=emp_code,
                    employee_code=emp_code,
                    first_name=data.get('first_name','').strip(),
                    middle_name=data.get('middle_name','').strip(),
                    last_name=data.get('last_name','').strip(),
                    official_email=email,
                    personal_email=data.get('personal_email','').strip(),
                    mobile=data.get('mobile','').strip(),
                    gender=data.get('gender','M'),
                    date_of_birth=data.get('date_of_birth') or None,
                    blood_group=data.get('blood_group',''),
                    marital_status=data.get('marital_status','single'),
                    nationality=data.get('nationality','Indian'),
                    department=dept,
                    designation=desig,
                    location=loc,
                    joining_date=data.get('joining_date') or timezone.now().date(),
                    employment_type=data.get('employment_type','permanent'),
                    status='active',
                    current_address=data.get('current_address',''),
                    permanent_address=data.get('permanent_address',''),
                    created_by=request.user,
                )
                messages.success(request, f'Employee {emp.get_full_name()} (Code: {emp_code}) created. Temp password: Welcome@123')
                return redirect('hr_admin:employee_detail', pk=emp.id)
        except (ValueError, Department.DoesNotExist, Designation.DoesNotExist, Location.DoesNotExist) as e:
            pass
        except Exception as e:
            messages.error(request, f'Error creating employee: {str(e)}')

    from apps.employees.models import Department, Designation, Location
    return render(request, 'hr_admin/employees/add.html', {
        'departments': Department.objects.filter(is_active=True).order_by('name'),
        'designations': Designation.objects.filter(is_active=True).order_by('name'),
        'locations': Location.objects.order_by('name'),
        'gender_choices': [('M','Male'),('F','Female'),('O','Other')],
        'blood_groups': ['A+','A-','B+','B-','O+','O-','AB+','AB-'],
        'employment_types': [('permanent','Permanent'),('contract','Contract'),('intern','Intern'),('probation','Probation')],
        'marital_choices': [('single','Single'),('married','Married'),('divorced','Divorced')],
    })


@admin_required
def employee_detail(request, pk):
    from apps.employees.models import Employee, EmergencyContact, EmployeeBank
    emp = get_object_or_404(Employee, id=pk)
    try:
        bank = emp.bank_details.first()
    except:
        bank = None
    try:
        emergency = emp.emergency_contacts.first()
    except:
        emergency = None
    return render(request, 'hr_admin/employees/detail.html', {
        'emp': emp, 'bank': bank, 'emergency': emergency,
    })


@admin_required
def employee_edit(request, pk):
    from apps.employees.models import Employee, Department, Designation, Location
    emp = get_object_or_404(Employee, id=pk)
    if request.method == 'POST':
        try:
            data = request.POST
            emp.first_name = data.get('first_name', emp.first_name).strip()
            emp.middle_name = data.get('middle_name', emp.middle_name).strip()
            emp.last_name = data.get('last_name', emp.last_name).strip()
            emp.mobile = data.get('mobile', emp.mobile).strip()
            emp.personal_email = data.get('personal_email', emp.personal_email).strip()
            emp.gender = data.get('gender', emp.gender)
            emp.blood_group = data.get('blood_group', emp.blood_group)
            emp.marital_status = data.get('marital_status', emp.marital_status)
            emp.nationality = data.get('nationality', emp.nationality)
            emp.current_address = data.get('current_address', emp.current_address)
            emp.permanent_address = data.get('permanent_address', emp.permanent_address)
            emp.city = data.get('city', emp.city)
            emp.state = data.get('state', emp.state)
            emp.pincode = data.get('pincode', emp.pincode)
            emp.employment_type = data.get('employment_type', emp.employment_type)
            emp.status = data.get('status', emp.status)
            if data.get('department'):
                emp.department = Department.objects.get(id=data['department'])
            if data.get('designation'):
                emp.designation = Designation.objects.get(id=data['designation'])
            if data.get('location'):
                emp.location = Location.objects.get(id=data['location'])
            if data.get('date_of_birth'):
                emp.date_of_birth = data['date_of_birth']
            if data.get('joining_date'):
                emp.joining_date = data['joining_date']
            emp.save()
            messages.success(request, f'Employee {emp.get_full_name()} updated successfully.')
            return redirect('hr_admin:employee_detail', pk=pk)
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

    return render(request, 'hr_admin/employees/edit.html', {
        'emp': emp,
        'departments': Department.objects.filter(is_active=True).order_by('name'),
        'designations': Designation.objects.filter(is_active=True).order_by('name'),
        'locations': Location.objects.order_by('name'),
        'gender_choices': [('M','Male'),('F','Female'),('O','Other')],
        'blood_groups': ['A+','A-','B+','B-','O+','O-','AB+','AB-'],
        'employment_types': [('permanent','Permanent'),('contract','Contract'),('intern','Intern'),('probation','Probation')],
        'status_choices': [('active','Active'),('inactive','Inactive'),('on_leave','On Leave'),('resigned','Resigned'),('terminated','Terminated')],
        'marital_choices': [('single','Single'),('married','Married'),('divorced','Divorced')],
    })


@admin_required
@require_http_methods(["POST"])
def employee_bulk_upload(request):
    """CSV bulk upload with full validation and error reporting"""
    from apps.employees.models import Employee, Department, Designation, Location
    from apps.authentication.models import User
    if 'csv_file' not in request.FILES:
        messages.error(request, 'Please select a CSV file.')
        return redirect('hr_admin:employee_list')

    f = request.FILES['csv_file']
    if not f.name.endswith('.csv'):
        messages.error(request, 'Only CSV files are allowed.')
        return redirect('hr_admin:employee_list')

    decoded = f.read().decode('utf-8-sig')
    reader = csv.DictReader(io.StringIO(decoded))

    REQUIRED = ['first_name','last_name','official_email','mobile','gender',
                'date_of_birth','joining_date','department_code','designation_name','location_code']

    # Validate headers
    headers = [h.strip().lower() for h in (reader.fieldnames or [])]
    missing = [r for r in REQUIRED if r not in headers]
    if missing:
        messages.error(request, f'Missing required columns: {", ".join(missing)}')
        return redirect('hr_admin:employee_bulk_upload_page')

    success_count, error_rows = 0, []

    for row_num, row in enumerate(reader, start=2):
        row = {k.strip().lower(): v.strip() for k, v in row.items()}
        row_errors = []

        # Validate required
        for field in REQUIRED:
            if not row.get(field):
                row_errors.append(f'{field} is required')

        if row_errors:
            error_rows.append({'row': row_num, 'errors': row_errors, 'data': row.get('official_email','')})
            continue

        try:
            with transaction.atomic():
                email = row['official_email'].lower()
                if User.objects.filter(email=email).exists():
                    error_rows.append({'row': row_num, 'errors': ['Email already exists'], 'data': email})
                    continue

                dept = Department.objects.filter(code__iexact=row['department_code']).first()
                if not dept:
                    error_rows.append({'row': row_num, 'errors': [f"Department '{row['department_code']}' not found"], 'data': email})
                    continue

                desig = Designation.objects.filter(
                    Q(name__iexact=row['designation_name']) | Q(code__iexact=row.get('designation_code',''))
                ).first()
                if not desig:
                    error_rows.append({'row': row_num, 'errors': [f"Designation '{row['designation_name']}' not found"], 'data': email})
                    continue

                loc = Location.objects.filter(code__iexact=row['location_code']).first()
                if not loc:
                    error_rows.append({'row': row_num, 'errors': [f"Location '{row['location_code']}' not found"], 'data': email})
                    continue

                user = User.objects.create_user(
                    email=email, password='Welcome@123', role='employee',
                )

                last = Employee.objects.order_by('-created_at').first()
                next_num = 1001
                if last and last.employee_code:
                    try: next_num = int(last.employee_code.replace('EMP','')) + 1
                    except: pass
                emp_code = f'EMP{next_num:04d}'

                Employee.objects.create(
                    user=user, employee_id=emp_code, employee_code=emp_code,
                    first_name=row['first_name'], last_name=row['last_name'],
                    middle_name=row.get('middle_name',''),
                    official_email=email, personal_email=row.get('personal_email',''),
                    mobile=row['mobile'],
                    gender=row['gender'].upper()[:1] or 'M',
                    date_of_birth=row['date_of_birth'],
                    blood_group=row.get('blood_group',''),
                    marital_status=row.get('marital_status','single'),
                    nationality=row.get('nationality','Indian'),
                    department=dept, designation=desig, location=loc,
                    joining_date=row['joining_date'],
                    employment_type=row.get('employment_type','permanent'),
                    current_address=row.get('current_address',''),
                    permanent_address=row.get('permanent_address',''),
                    status='active', created_by=request.user,
                )
                success_count += 1
        except Exception as e:
            error_rows.append({'row': row_num, 'errors': [str(e)], 'data': row.get('official_email','')})

    return render(request, 'hr_admin/employees/bulk_upload_result.html', {
        'success_count': success_count,
        'error_rows': error_rows,
        'total': success_count + len(error_rows),
    })


@admin_required
def employee_bulk_upload_page(request):
    from apps.employees.models import Department, Designation, Location
    columns = [
        {'col':'first_name',       'req':True,  'ex':'Rahul',                     'note':'Employee first name'},
        {'col':'middle_name',      'req':False, 'ex':'Kumar',                     'note':'Middle name (optional)'},
        {'col':'last_name',        'req':True,  'ex':'Sharma',                    'note':'Employee last name'},
        {'col':'official_email',   'req':True,  'ex':'rahul@company.com',         'note':'Must be unique — becomes login email'},
        {'col':'personal_email',   'req':False, 'ex':'rahul@gmail.com',           'note':'Personal email (optional)'},
        {'col':'mobile',           'req':True,  'ex':'9876543210',                'note':'10-digit mobile number'},
        {'col':'gender',           'req':True,  'ex':'M',                         'note':'M / F / O'},
        {'col':'date_of_birth',    'req':True,  'ex':'1990-05-15',                'note':'Format: YYYY-MM-DD'},
        {'col':'blood_group',      'req':False, 'ex':'B+',                        'note':'A+/A-/B+/B-/O+/O-/AB+/AB-'},
        {'col':'marital_status',   'req':False, 'ex':'married',                   'note':'single/married/divorced/widowed'},
        {'col':'nationality',      'req':False, 'ex':'Indian',                    'note':'Default: Indian'},
        {'col':'department_code',  'req':True,  'ex':'TECH',                      'note':'Must match existing department code'},
        {'col':'designation_name', 'req':True,  'ex':'Software Engineer',         'note':'Must match existing designation name'},
        {'col':'location_code',    'req':True,  'ex':'HYD',                       'note':'Must match existing location code'},
        {'col':'joining_date',     'req':True,  'ex':'2024-01-10',                'note':'Format: YYYY-MM-DD'},
        {'col':'employment_type',  'req':False, 'ex':'permanent',                 'note':'permanent/contract/intern/probation'},
        {'col':'current_address',  'req':False, 'ex':'Plot 12 HITEC City, Hyd',  'note':'Current residential address'},
        {'col':'permanent_address','req':False, 'ex':'Same as above',             'note':'Permanent address'},
    ]
    return render(request, 'hr_admin/employees/bulk_upload.html', {
        'departments': Department.objects.filter(is_active=True).order_by('name'),
        'designations': Designation.objects.filter(is_active=True).order_by('name'),
        'locations': Location.objects.order_by('name'),
        'columns': columns,
    })


@admin_required
def employee_csv_template(request):
    """Download CSV template with headers and sample row"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="employee_bulk_upload_template.csv"'
    writer = csv.writer(response)
    writer.writerow([
        'first_name','middle_name','last_name','official_email','personal_email',
        'mobile','gender','date_of_birth','blood_group','marital_status','nationality',
        'department_code','designation_name','location_code','joining_date',
        'employment_type','current_address','permanent_address',
    ])
    writer.writerow([
        'Rahul','Kumar','Sharma','rahul.sharma@company.com','rahul@gmail.com',
        '9876543210','M','1990-05-15','B+','married','Indian',
        'TECH','Software Engineer','HYD','2024-01-10',
        'permanent','Plot 12 Banjara Hills Hyderabad','Plot 12 Banjara Hills Hyderabad',
    ])
    return response


# ─────────────────────────────────────────────
# DEPARTMENT MANAGEMENT
# ─────────────────────────────────────────────
@admin_required
def department_list(request):
    from apps.employees.models import Department
    depts = Department.objects.annotate(emp_count=Count('employees')).order_by('name')
    return render(request, 'hr_admin/departments/list.html', {'departments': depts})


@admin_required
def department_add(request):
    from apps.employees.models import Department
    if request.method == 'POST':
        try:
            d = request.POST
            if Department.objects.filter(code=d.get('code','')).exists():
                messages.error(request, 'Department code already exists.')
            else:
                dept = Department.objects.create(
                    name=d['name'].strip(), code=d['code'].strip().upper(),
                    description=d.get('description','').strip(), is_active=True,
                )
                messages.success(request, f'Department "{dept.name}" created.')
                return redirect('hr_admin:department_list')
        except Exception as e:
            messages.error(request, str(e))
    return render(request, 'hr_admin/departments/form.html', {'action': 'Add', 'dept': None})


@admin_required
def department_edit(request, pk):
    from apps.employees.models import Department
    dept = get_object_or_404(Department, id=pk)
    if request.method == 'POST':
        d = request.POST
        dept.name = d.get('name', dept.name).strip()
        dept.code = d.get('code', dept.code).strip().upper()
        dept.description = d.get('description', dept.description).strip()
        dept.is_active = d.get('is_active') == 'on'
        dept.save()
        messages.success(request, f'Department "{dept.name}" updated.')
        return redirect('hr_admin:department_list')
    return render(request, 'hr_admin/departments/form.html', {'action': 'Edit', 'dept': dept})


@admin_required
def department_bulk_upload(request):
    from apps.employees.models import Department
    if request.method == 'POST' and 'csv_file' in request.FILES:
        f = request.FILES['csv_file']
        reader = csv.DictReader(io.StringIO(f.read().decode('utf-8-sig')))
        ok, errors = 0, []
        for i, row in enumerate(reader, 2):
            name = row.get('name','').strip()
            code = row.get('code','').strip().upper()
            if not name or not code:
                errors.append(f'Row {i}: name and code required')
                continue
            obj, created = Department.objects.get_or_create(code=code, defaults={'name':name,'is_active':True})
            if created: ok += 1
            else: errors.append(f'Row {i}: code {code} already exists')
        messages.success(request, f'{ok} departments imported. {len(errors)} errors.')
    return render(request, 'hr_admin/departments/bulk_upload.html')


@admin_required
def department_csv_template(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="department_template.csv"'
    w = csv.writer(response)
    w.writerow(['name','code','description'])
    w.writerow(['Technology','TECH','Software and IT team'])
    w.writerow(['Human Resources','HR','HR department'])
    w.writerow(['Finance','FIN','Finance and accounts'])
    return response


# ─────────────────────────────────────────────
# DESIGNATION MANAGEMENT
# ─────────────────────────────────────────────
@admin_required
def designation_list(request):
    from apps.employees.models import Designation
    desigs = Designation.objects.select_related('department').annotate(emp_count=Count('employees')).order_by('department__name','name')
    return render(request, 'hr_admin/designations/list.html', {'designations': desigs})


@admin_required
def designation_add(request):
    from apps.employees.models import Department, Designation
    if request.method == 'POST':
        d = request.POST
        try:
            dept = Department.objects.get(id=d['department'])
            Designation.objects.create(
                name=d['name'].strip(), code=d.get('code','').strip().upper(),
                department=dept, grade=d.get('grade',''), level=int(d.get('level',1) or 1),
                is_active=True,
            )
            messages.success(request, 'Designation created.')
            return redirect('hr_admin:designation_list')
        except Exception as e:
            messages.error(request, str(e))
    return render(request, 'hr_admin/designations/form.html', {
        'action':'Add', 'desig':None,
        'departments': __import__('apps.employees.models', fromlist=['Department']).Department.objects.filter(is_active=True).order_by('name')
    })


@admin_required
def designation_edit(request, pk):
    from apps.employees.models import Designation, Department
    desig = get_object_or_404(Designation, id=pk)
    if request.method == 'POST':
        d = request.POST
        desig.name = d.get('name', desig.name).strip()
        desig.code = d.get('code', desig.code).strip().upper()
        desig.grade = d.get('grade', desig.grade)
        desig.level = int(d.get('level', desig.level) or 1)
        desig.is_active = d.get('is_active') == 'on'
        if d.get('department'):
            desig.department = Department.objects.get(id=d['department'])
        desig.save()
        messages.success(request, 'Designation updated.')
        return redirect('hr_admin:designation_list')
    return render(request, 'hr_admin/designations/form.html', {
        'action':'Edit', 'desig':desig,
        'departments': Department.objects.filter(is_active=True).order_by('name'),
    })


@admin_required
def designation_csv_template(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="designation_template.csv"'
    w = csv.writer(response)
    w.writerow(['name','code','department_code','grade','level'])
    w.writerow(['Software Engineer','SE','TECH','L2','Junior'])
    w.writerow(['Senior Engineer','SSE','TECH','L3','Mid'])
    w.writerow(['HR Manager','HRM','HR','M1','Manager'])
    return response


@admin_required
def designation_bulk_upload(request):
    from apps.employees.models import Designation, Department
    if request.method == 'POST' and 'csv_file' in request.FILES:
        f = request.FILES['csv_file']
        reader = csv.DictReader(io.StringIO(f.read().decode('utf-8-sig')))
        ok, errors = 0, []
        for i, row in enumerate(reader, 2):
            name = row.get('name','').strip()
            dept_code = row.get('department_code','').strip()
            if not name or not dept_code:
                errors.append(f'Row {i}: name and department_code required'); continue
            dept = Department.objects.filter(code__iexact=dept_code).first()
            if not dept:
                errors.append(f'Row {i}: department {dept_code} not found'); continue
            obj, created = Designation.objects.get_or_create(
                name=name, department=dept,
                defaults={'grade':row.get('grade',''),'level':int(row.get('level',1) or 1),'is_active':True}
            )
            if created: ok += 1
            else: errors.append(f'Row {i}: {name} in {dept_code} already exists')
        messages.success(request, f'{ok} designations imported. {len(errors)} errors.')
    return render(request, 'hr_admin/designations/bulk_upload.html')


# ─────────────────────────────────────────────
# LOCATION MANAGEMENT
# ─────────────────────────────────────────────
@admin_required
def location_list(request):
    from apps.employees.models import Location
    locs = Location.objects.annotate(emp_count=Count('employees')).order_by('name')
    return render(request, 'hr_admin/locations/list.html', {'locations': locs})


@admin_required
def location_add(request):
    from apps.employees.models import Location
    if request.method == 'POST':
        d = request.POST
        try:
            Location.objects.create(
                name=d['name'].strip(), code=d['code'].strip().upper(),
                city=d.get('city',''), state=d.get('state',''),
                country=d.get('country','India'), pincode=d.get('pincode',''),
                address=d.get('address',''),
                latitude=d.get('latitude') or None, longitude=d.get('longitude') or None,
                geo_fence_radius=int(d.get('geo_fence_radius',100)),
            )
            messages.success(request, 'Location created.')
            return redirect('hr_admin:location_list')
        except Exception as e:
            messages.error(request, str(e))
    return render(request, 'hr_admin/locations/form.html', {'action':'Add','loc':None})


@admin_required
def location_edit(request, pk):
    from apps.employees.models import Location
    loc = get_object_or_404(Location, id=pk)
    if request.method == 'POST':
        d = request.POST
        loc.name=d.get('name',loc.name).strip(); loc.code=d.get('code',loc.code).strip().upper()
        loc.city=d.get('city',loc.city); loc.state=d.get('state',loc.state)
        loc.country=d.get('country',loc.country); loc.pincode=d.get('pincode',loc.pincode)
        loc.address=d.get('address',loc.address)
        if d.get('latitude'): loc.latitude=float(d['latitude'])
        if d.get('longitude'): loc.longitude=float(d['longitude'])
        loc.geo_fence_radius=int(d.get('geo_fence_radius',loc.geo_fence_radius))
        loc.save()
        messages.success(request, 'Location updated.')
        return redirect('hr_admin:location_list')
    return render(request, 'hr_admin/locations/form.html', {'action':'Edit','loc':loc})


@admin_required
def location_csv_template(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="location_template.csv"'
    w = csv.writer(response)
    w.writerow(['name','code','city','state','country','pincode','address','latitude','longitude','geo_fence_radius'])
    w.writerow(['Hyderabad HQ','HYD','Hyderabad','Telangana','India','500081','Plot 1 HITEC City','17.4474','78.3762','100'])
    return response


@admin_required
def location_bulk_upload(request):
    from apps.employees.models import Location
    if request.method == 'POST' and 'csv_file' in request.FILES:
        f = request.FILES['csv_file']
        reader = csv.DictReader(io.StringIO(f.read().decode('utf-8-sig')))
        ok, errors = 0, []
        for i, row in enumerate(reader, 2):
            name = row.get('name','').strip(); code = row.get('code','').strip().upper()
            if not name or not code:
                errors.append(f'Row {i}: name and code required'); continue
            obj, created = Location.objects.get_or_create(
                code=code, defaults={
                    'name':name,'city':row.get('city',''),'state':row.get('state',''),
                    'country':row.get('country','India'),'pincode':row.get('pincode',''),
                    'address':row.get('address',''),
                    'geo_fence_radius':int(row.get('geo_fence_radius',100) or 100),
                }
            )
            if created: ok += 1
            else: errors.append(f'Row {i}: code {code} already exists')
        messages.success(request, f'{ok} locations imported.')
    return render(request, 'hr_admin/locations/bulk_upload.html')


# ─────────────────────────────────────────────
# USER MANAGEMENT
# ─────────────────────────────────────────────
@admin_required
def user_list(request):
    from apps.authentication.models import User
    qs = User.objects.order_by('-date_joined')
    q = request.GET.get('q','').strip()
    role = request.GET.get('role','')
    if q:
        qs = qs.filter(
            Q(email__icontains=q) |
            Q(employee_profile__first_name__icontains=q) |
            Q(employee_profile__last_name__icontains=q)
        ).distinct()
    if role: qs = qs.filter(role=role)
    from apps.authentication.models import User as U
    return render(request, 'hr_admin/users/list.html', {
        'users': qs[:200], 'search': q, 'role_filter': role,
        'role_choices': U.ROLE_CHOICES,
    })


@admin_required
def user_add(request):
    from apps.authentication.models import User
    if request.method == 'POST':
        d = request.POST
        email = d.get('email','').strip().lower()
        if User.objects.filter(email=email).exists():
            messages.error(request, 'User with this email already exists.')
        else:
            try:
                user = User.objects.create_user(
                    email=email, password=d.get('password','Welcome@123'),
                    role=d.get('role','employee'),
                    is_active=d.get('is_active')=='on',
                    is_staff=d.get('role') in ('super_admin','hr_admin'),
                )
                messages.success(request, f'User {email} created.')
                return redirect('hr_admin:user_list')
            except Exception as e:
                messages.error(request, str(e))
    from apps.authentication.models import User as U
    return render(request, 'hr_admin/users/form.html', {'action':'Add','u':None,'role_choices':U.ROLE_CHOICES})


@admin_required
def user_edit(request, pk):
    from apps.authentication.models import User
    u = get_object_or_404(User, id=pk)
    if request.method == 'POST':
        d = request.POST
        try:
            employee = u.employee_profile
            employee.first_name = d.get('first_name', employee.first_name)
            employee.last_name = d.get('last_name', employee.last_name)
            employee.save(update_fields=['first_name', 'last_name', 'updated_at'])
        except Exception:
            pass
        u.role=d.get('role',u.role)
        u.is_active=d.get('is_active')=='on'
        u.is_staff=u.role in ('super_admin','hr_admin')
        if d.get('new_password'):
            u.set_password(d['new_password'])
        u.save()
        messages.success(request, f'User {u.email} updated.')
        return redirect('hr_admin:user_list')
    return render(request, 'hr_admin/users/form.html', {'action':'Edit','u':u,'role_choices':User.ROLE_CHOICES})


# ─────────────────────────────────────────────
# LEAVE TYPE MANAGEMENT
# ─────────────────────────────────────────────
@admin_required
def leave_type_list(request):
    from apps.leave_management.models import LeaveType
    lts = LeaveType.objects.order_by('name')
    return render(request, 'hr_admin/leave_types/list.html', {'leave_types': lts})


@admin_required
def leave_type_add(request):
    from apps.leave_management.models import LeaveType
    if request.method == 'POST':
        d = request.POST
        try:
            lt = LeaveType.objects.create(
                name=d['name'].strip(), code=d['code'].strip().upper(),
                category=d.get('category','casual'),
                days_allowed_per_year=float(d.get('days_allowed_per_year',12)),
                max_carry_forward=float(d.get('max_carry_forward',0)),
                is_paid=d.get('is_paid')=='on',
                allow_half_day=d.get('allow_half_day')=='on',
                requires_document=d.get('requires_document')=='on',
                color=d.get('color','#3B82F6'),
                is_active=True,
            )
            messages.success(request, f'Leave type "{lt.name}" created.')
            return redirect('hr_admin:leave_type_list')
        except Exception as e:
            messages.error(request, str(e))
    return render(request, 'hr_admin/leave_types/form.html', {'action':'Add','lt':None})


@admin_required
def leave_type_edit(request, pk):
    from apps.leave_management.models import LeaveType
    lt = get_object_or_404(LeaveType, id=pk)
    if request.method == 'POST':
        d = request.POST
        lt.name=d.get('name',lt.name).strip(); lt.code=d.get('code',lt.code).strip().upper()
        lt.category=d.get('category',lt.category)
        lt.days_allowed_per_year=float(d.get('days_allowed_per_year',lt.days_allowed_per_year))
        lt.max_carry_forward=float(d.get('max_carry_forward',lt.max_carry_forward))
        lt.is_paid=d.get('is_paid')=='on'; lt.allow_half_day=d.get('allow_half_day')=='on'
        lt.requires_document=d.get('requires_document')=='on'
        lt.color=d.get('color',lt.color); lt.is_active=d.get('is_active')=='on'
        lt.save()
        messages.success(request, 'Leave type updated.')
        return redirect('hr_admin:leave_type_list')
    return render(request, 'hr_admin/leave_types/form.html', {'action':'Edit','lt':lt})


# ─────────────────────────────────────────────
# ATTENDANCE MANAGEMENT
# ─────────────────────────────────────────────
@admin_required
def attendance_list(request):
    from apps.attendance.models import Attendance
    from apps.employees.models import Department, Employee
    from datetime import date, timedelta
    today = timezone.now().date()
    date_from = request.GET.get('date_from', (today - timezone.timedelta(days=6)).isoformat())
    date_to = request.GET.get('date_to', today.isoformat())
    dept_id = request.GET.get('dept','')
    status_f = request.GET.get('status','')
    search = request.GET.get('q','')

    qs = Attendance.objects.select_related('employee','employee__department').order_by('-date','employee__first_name')
    if date_from: qs = qs.filter(date__gte=date_from)
    if date_to: qs = qs.filter(date__lte=date_to)
    if dept_id: qs = qs.filter(employee__department_id=dept_id)
    if status_f: qs = qs.filter(status=status_f)
    if search: qs = qs.filter(Q(employee__first_name__icontains=search)|Q(employee__last_name__icontains=search))

    records = list(qs[:500])
    # Missing weekdays are displayed as absent, but are never saved as rows.
    try:
        first_date = date.fromisoformat(date_from)
        last_date = date.fromisoformat(date_to)
    except (TypeError, ValueError):
        first_date, last_date = today - timedelta(days=6), today

    employees = Employee.objects.filter(status='active')
    if dept_id:
        employees = employees.filter(department_id=dept_id)
    if search:
        employees = employees.filter(Q(first_name__icontains=search) | Q(last_name__icontains=search))
    existing = {(record.employee_id, record.date) for record in records}
    if not status_f or status_f == 'absent':
        for current_date in (first_date + timedelta(days=offset)
                             for offset in range((last_date - first_date).days + 1)):
            if current_date > today or current_date.weekday() >= 5:
                continue
            for employee in employees.select_related('department'):
                if (employee.id, current_date) in existing:
                    continue
                records.append(type('MissingAttendance', (), {
                    'employee': employee,
                    'date': current_date,
                    'clock_in': None,
                    'clock_out': None,
                    'effective_working_minutes': 0,
                    'status': 'absent',
                    'get_status_display': lambda self: 'Absent',
                })())
    records.sort(key=lambda record: (record.date, record.employee.first_name), reverse=True)
    return render(request, 'hr_admin/attendance/list.html', {
        'records': records[:500], 'total': len(records),
        'departments': Department.objects.filter(is_active=True).order_by('name'),
        'date_from': date_from, 'date_to': date_to,
        'dept_id': dept_id, 'status_f': status_f, 'search': search,
    })


@admin_required
def attendance_approvals(request):
    """Pending attendance punches awaiting admin/HR approval."""
    from apps.attendance.models import Attendance
    status_f = request.GET.get('status', 'pending')
    qs = Attendance.objects.select_related('employee', 'employee__department', 'approved_by').order_by('-date', '-clock_in')
    if status_f:
        qs = qs.filter(approval_status=status_f)
    return render(request, 'hr_admin/attendance/approvals.html', {
        'records': qs[:300],
        'status_f': status_f,
        'pending_count': Attendance.objects.filter(approval_status='pending').count(),
    })


@admin_required
@require_http_methods(["POST"])
def attendance_approve_action(request, pk):
    """HR/Admin approves or rejects one attendance punch from the web UI."""
    from apps.attendance.models import Attendance
    attendance = get_object_or_404(Attendance, id=pk)
    decision = request.POST.get('decision')
    if decision not in ('approved', 'rejected'):
        messages.error(request, 'Invalid decision.')
        return redirect('hr_admin:attendance_approvals')

    attendance.approval_status = decision
    attendance.approved_by = request.user
    attendance.approved_at = timezone.now()
    attendance.approval_remarks = request.POST.get('remarks', '')
    if decision == 'rejected':
        attendance.admin_remarks = (attendance.admin_remarks + '\n' if attendance.admin_remarks else '') + \
            f"Rejected by {request.user.email} on {timezone.now().strftime('%Y-%m-%d %H:%M')}: {attendance.approval_remarks}"
    attendance.save(update_fields=['approval_status', 'approved_by', 'approved_at', 'approval_remarks', 'admin_remarks'])

    messages.success(request, f"Attendance for {attendance.employee.get_full_name()} on {attendance.date} {decision}.")
    return redirect('hr_admin:attendance_approvals')


@admin_required
def attendance_bulk_upload(request):
    from apps.attendance.models import Attendance
    from apps.employees.models import Employee
    if request.method == 'POST' and 'csv_file' in request.FILES:
        f = request.FILES['csv_file']
        reader = csv.DictReader(io.StringIO(f.read().decode('utf-8-sig')))
        ok, errors = 0, []
        for i, row in enumerate(reader, 2):
            emp_code = row.get('employee_code','').strip()
            date_str = row.get('date','').strip()
            if not emp_code or not date_str:
                errors.append(f'Row {i}: employee_code and date required'); continue
            emp = Employee.objects.filter(employee_code=emp_code).first()
            if not emp:
                errors.append(f'Row {i}: Employee {emp_code} not found'); continue
            try:
                from datetime import date, time as dtime, datetime
                att_date = date.fromisoformat(date_str)
                cin_str = row.get('clock_in','').strip()
                cout_str = row.get('clock_out','').strip()
                ci = dtime.fromisoformat(cin_str) if cin_str else None
                co = dtime.fromisoformat(cout_str) if cout_str else None
                obj, created = Attendance.objects.get_or_create(
                    employee=emp, date=att_date,
                    defaults={
                        'clock_in': datetime.combine(att_date, ci) if ci else None,
                        'clock_out': datetime.combine(att_date, co) if co else None,
                        'status': row.get('status','present'),
                        'clock_in_source': 'admin',
                        'clock_out_source': 'admin',
                        # HR/Admin entering attendance directly is itself
                        # the approval — no separate review needed.
                        'approval_status': 'approved',
                        'approved_by': request.user,
                        'approved_at': timezone.now(),
                    }
                )
                if created: ok += 1
                else: errors.append(f'Row {i}: Attendance for {emp_code} on {date_str} already exists')
            except Exception as e:
                errors.append(f'Row {i}: {str(e)}')
        messages.success(request, f'{ok} records uploaded. {len(errors)} errors.')
    return render(request, 'hr_admin/attendance/bulk_upload.html')


@admin_required
def attendance_csv_template(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="attendance_template.csv"'
    w = csv.writer(response)
    w.writerow(['employee_code','date','clock_in','clock_out','status'])
    w.writerow(['EMP1001','2025-06-01','09:00','18:00','present'])
    w.writerow(['EMP1002','2025-06-01','09:30','18:00','late_mark'])
    w.writerow(['EMP1003','2025-06-01','','','absent'])
    return response


# ─────────────────────────────────────────────
# LEAVE MANAGEMENT (ADMIN)
# ─────────────────────────────────────────────
@admin_required
def leave_list(request):
    from apps.leave_management.models import LeaveApplication
    from apps.employees.models import Department
    qs = LeaveApplication.objects.select_related('employee','employee__department','leave_type').order_by('-from_date')
    dept_id = request.GET.get('dept',''); status_f = request.GET.get('status','')
    if dept_id: qs = qs.filter(employee__department_id=dept_id)
    if status_f: qs = qs.filter(status=status_f)
    return render(request, 'hr_admin/leaves/list.html', {
        'applications': qs[:300],
        'departments': Department.objects.filter(is_active=True).order_by('name'),
        'dept_id': dept_id, 'status_f': status_f,
    })


@admin_required
def leave_bulk_upload(request):
    from apps.leave_management.models import LeaveApplication, LeaveType
    from apps.employees.models import Employee
    if request.method == 'POST' and 'csv_file' in request.FILES:
        f = request.FILES['csv_file']
        reader = csv.DictReader(io.StringIO(f.read().decode('utf-8-sig')))
        ok, errors = 0, []
        for i, row in enumerate(reader, 2):
            emp_code = row.get('employee_code','').strip()
            lt_code = row.get('leave_type_code','').strip()
            from_date = row.get('from_date','').strip()
            to_date = row.get('to_date','').strip()
            if not all([emp_code, lt_code, from_date, to_date]):
                errors.append(f'Row {i}: employee_code, leave_type_code, from_date, to_date required'); continue
            emp = Employee.objects.filter(employee_code=emp_code).first()
            if not emp: errors.append(f'Row {i}: Employee {emp_code} not found'); continue
            lt = LeaveType.objects.filter(code__iexact=lt_code).first()
            if not lt: errors.append(f'Row {i}: Leave type {lt_code} not found'); continue
            try:
                from datetime import date
                fd = date.fromisoformat(from_date); td = date.fromisoformat(to_date)
                days = (td - fd).days + 1
                import datetime
                app = LeaveApplication.objects.create(
                    employee=emp, leave_type=lt,
                    from_date=fd, to_date=td, total_days=days,
                    reason=row.get('reason','Bulk imported'),
                    status=row.get('status','approved'),
                )
                ok += 1
            except Exception as e:
                errors.append(f'Row {i}: {str(e)}')
        messages.success(request, f'{ok} leave records imported.')
    return render(request, 'hr_admin/leaves/bulk_upload.html')


@admin_required
def leave_csv_template(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="leave_template.csv"'
    w = csv.writer(response)
    w.writerow(['employee_code','leave_type_code','from_date','to_date','reason','status'])
    w.writerow(['EMP1001','CL','2025-06-10','2025-06-11','Personal work','approved'])
    w.writerow(['EMP1002','SL','2025-06-15','2025-06-15','Sick','approved'])
    return response
