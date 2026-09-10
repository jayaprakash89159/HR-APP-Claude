from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import path

from .models import ApprovalAssignment, ApprovalModule, ApprovalRule, ApprovalWorkflow, SwipeRequest


@admin.register(ApprovalModule)
class ApprovalModuleAdmin(admin.ModelAdmin):
    list_display = ('label', 'name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('label', 'name')
    change_list_template = 'admin/workflow/approvalmodule/change_list.html'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'approval-flow/',
                self.admin_site.admin_view(self.approval_flow_view),
                name='workflow_approvalmodule_approval_flow',
            ),
        ]
        return custom_urls + urls

    def approval_flow_view(self, request):
        modules = ApprovalModule.objects.prefetch_related('rules__assignments').all()
        context = {
            **self.admin_site.each_context(request),
            'title': 'Approval Flow Configuration',
            'opts': self.model._meta,
            'modules': modules,
            'has_add_permission': self.has_add_permission(request),
            'has_change_permission': self.has_change_permission(request),
            'has_delete_permission': self.has_delete_permission(request),
            'has_view_permission': self.has_view_permission(request),
        }
        return TemplateResponse(request, 'admin/workflow/approvalmodule/approval_flow.html', context)


@admin.register(ApprovalRule)
class ApprovalRuleAdmin(admin.ModelAdmin):
    list_display = ('module', 'level_number', 'name', 'approver_role', 'is_active')
    list_filter = ('module', 'level_number', 'approver_role', 'is_active')
    search_fields = ('name', 'module__label')


@admin.register(ApprovalAssignment)
class ApprovalAssignmentAdmin(admin.ModelAdmin):
    list_display = ('module', 'rule', 'user', 'department', 'employee', 'is_active')
    list_filter = ('module', 'rule', 'is_active')
    search_fields = ('user__email', 'employee__first_name', 'department__name')


@admin.register(SwipeRequest)
class SwipeRequestAdmin(admin.ModelAdmin):
    list_display = ('employee', 'request_type', 'status', 'current_level', 'reviewed_by', 'created_at')
    list_filter = ('request_type', 'status', 'current_level')
    search_fields = ('employee__first_name', 'employee__last_name', 'reason')


@admin.register(ApprovalWorkflow)
class ApprovalWorkflowAdmin(admin.ModelAdmin):
    list_display = ('module', 'employee', 'current_level', 'status')
    list_filter = ('module', 'status')
    search_fields = ('employee__first_name', 'employee__last_name')
