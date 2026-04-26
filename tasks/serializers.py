from rest_framework import serializers

from users.serializers import UserSerializer
from users.models import User

from .models import Task


class TaskSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    assigned_to = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    assigned_to_detail = UserSerializer(source="assigned_to", read_only=True)

    class Meta:
        model = Task
        fields = (
            "id",
            "title",
            "description",
            "created_by",
            "assigned_to",
            "assigned_to_detail",
            "status",
            "created_at",
        )
        read_only_fields = ("id", "created_by", "created_at")

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)

    def validate_assigned_to(self, value):
        request = self.context["request"]
        if request.user.role != User.Roles.MANAGER and value != request.user:
            raise serializers.ValidationError("Employees can assign tasks only to themselves.")
        return value

    def validate_status(self, value):
        request = self.context["request"]
        instance = getattr(self, "instance", None)
        if (
            instance
            and request.user.role != User.Roles.MANAGER
            and instance.assigned_to_id != request.user.id
            and value != instance.status
        ):
            raise serializers.ValidationError("Only the assigned employee or a manager can change status.")
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        request = self.context["request"]
        instance = getattr(self, "instance", None)
        if (
            instance
            and request.user.role != User.Roles.MANAGER
            and instance.created_by_id != request.user.id
        ):
            locked_fields = ("title", "description", "assigned_to")
            changed = [field for field in locked_fields if field in attrs and attrs[field] != getattr(instance, field)]
            if changed:
                raise serializers.ValidationError(
                    "Only the task creator or a manager can edit title, description, or assignee."
                )
        return attrs
