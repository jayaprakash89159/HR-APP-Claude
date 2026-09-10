from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from apps.api.utils import health_check

admin.site.site_header = "WorkSphere HR Administration"
admin.site.site_title  = "WorkSphere HR"
admin.site.index_title = "Enterprise HR Management"

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Web pages
    path('',            include('apps.dashboard.urls')),
    path('auth/',       include('apps.authentication.urls')),
    path('employees/',  include('apps.employees.urls')),
    path('attendance/', include('apps.attendance.urls')),
    path('leave/',      include('apps.leave_management.urls')),
    path('payroll/',    include('apps.payroll.urls')),
    path('shifts/',     include('apps.shifts.urls')),
    path('reports/',    include('apps.reports.urls')),
    path('hr/',         include('apps.dashboard.hr_urls')),
    path('manage/',     include(('apps.hr_admin.urls', 'hr_admin'), namespace='hr_admin')),

    # REST API v1
    path('api/v1/', include([
        path('auth/',          include('apps.authentication.api_urls')),
        path('employees/',     include('apps.employees.api_urls')),
        path('attendance/',    include('apps.attendance.api_urls')),
        path('leave/',         include('apps.leave_management.api_urls')),
        path('payroll/',       include('apps.payroll.api_urls')),
        path('shifts/',        include('apps.shifts.api_urls')),
        path('reports/',       include('apps.reports.api_urls')),
        path('notifications/', include('apps.notifications.api_urls')),
        path('dashboard/',     include('apps.dashboard.api_urls')),
        path('workflow/',      include('apps.workflow.api_urls')),
    ])),

    # API docs
    path('api/schema/', SpectacularAPIView.as_view(),   name='schema'),
    path('api/docs/',   SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/',  SpectacularRedocView.as_view(url_name='schema'),   name='redoc'),

    # Health check
    path('health/', health_check, name='health_check'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,  document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
