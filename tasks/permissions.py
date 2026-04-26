from rest_framework.permissions import BasePermission

from users.models import User


class IsManagerOrRelatedTaskUser(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.user.role == User.Roles.MANAGER:
            return True
        is_related = obj.created_by_id == request.user.id or obj.assigned_to_id == request.user.id
        if not is_related:
            return False
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        if request.method == "DELETE":
            return obj.created_by_id == request.user.id
        return obj.created_by_id == request.user.id or obj.assigned_to_id == request.user.id
