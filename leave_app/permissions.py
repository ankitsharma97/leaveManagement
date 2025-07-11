from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.employee == request.user or request.user.role == 'hr'

class IsManagerOfEmployee(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.employee.manager == request.user or request.user.role == 'hr'

class IsHR(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'hr'

class IsManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'manager'

class IsEmployee(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'employee' 