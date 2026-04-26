from django import forms

from .models import Task


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ("title", "description", "assigned_to", "status")

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and getattr(user, "role", None) != "manager":
            self.fields["assigned_to"].queryset = user.__class__.objects.filter(pk=user.pk)
            if self.instance and self.instance.pk and self.instance.created_by_id != user.pk:
                self.fields["title"].disabled = True
                self.fields["description"].disabled = True
                self.fields["assigned_to"].disabled = True


class TaskUpdateForm(TaskForm):
    pass
