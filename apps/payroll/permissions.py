from rest_framework.permissions import BasePermission


class CanManagePayroll(BasePermission):
    message = 'Payroll administrator access is required.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.can_manage_payroll)