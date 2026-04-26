import pytest
from rest_framework.test import APIClient

from users.models import User

from .models import Task


@pytest.mark.django_db
def test_employee_creates_task_for_self_only():
    employee = User.objects.create_user(
        username="employee",
        email="employee@example.com",
        password="strongpass123",
        role=User.Roles.EMPLOYEE,
    )
    other = User.objects.create_user(
        username="other",
        email="other@example.com",
        password="strongpass123",
        role=User.Roles.EMPLOYEE,
    )
    client = APIClient()
    client.force_authenticate(user=employee)

    denied = client.post(
        "/api/tasks/",
        {
            "title": "Wrong assignee",
            "description": "x",
            "assigned_to": other.id,
            "status": Task.Status.TODO,
        },
        format="json",
    )
    allowed = client.post(
        "/api/tasks/",
        {
            "title": "My task",
            "description": "x",
            "assigned_to": employee.id,
            "status": Task.Status.TODO,
        },
        format="json",
    )

    assert denied.status_code == 400
    assert allowed.status_code == 201
    assert Task.objects.filter(created_by=employee, assigned_to=employee).count() == 1


@pytest.mark.django_db
def test_assigned_employee_can_only_change_status():
    creator = User.objects.create_user(
        username="creator",
        email="creator@example.com",
        password="strongpass123",
        role=User.Roles.EMPLOYEE,
    )
    assignee = User.objects.create_user(
        username="assignee",
        email="assignee@example.com",
        password="strongpass123",
        role=User.Roles.EMPLOYEE,
    )
    task = Task.objects.create(
        title="Original title",
        description="Original description",
        created_by=creator,
        assigned_to=assignee,
        status=Task.Status.TODO,
    )
    client = APIClient()
    client.force_authenticate(user=assignee)

    forbidden = client.put(
        f"/api/tasks/{task.id}/",
        {
            "title": "Changed title",
            "description": "Changed description",
            "assigned_to": assignee.id,
            "status": Task.Status.IN_PROGRESS,
        },
        format="json",
    )
    allowed = client.patch(
        f"/api/tasks/{task.id}/",
        {
            "status": Task.Status.IN_PROGRESS,
        },
        format="json",
    )

    assert forbidden.status_code == 400
    assert allowed.status_code == 200
    task.refresh_from_db()
    assert task.title == "Original title"
    assert task.status == Task.Status.IN_PROGRESS
