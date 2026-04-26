import pytest
from rest_framework.test import APIClient

from tasks.models import Task
from tracking.services import start_timer, stop_timer
from users.models import User


@pytest.mark.django_db
def test_manager_can_filter_daily_report_by_user():
    manager = User.objects.create_user(
        username="manager",
        email="manager@example.com",
        password="strongpass123",
        role=User.Roles.MANAGER,
    )
    employee_one = User.objects.create_user(
        username="one",
        email="one@example.com",
        password="strongpass123",
        role=User.Roles.EMPLOYEE,
    )
    employee_two = User.objects.create_user(
        username="two",
        email="two@example.com",
        password="strongpass123",
        role=User.Roles.EMPLOYEE,
    )
    first_task = Task.objects.create(title="Task A", description="x", created_by=manager, assigned_to=employee_one)
    second_task = Task.objects.create(title="Task B", description="y", created_by=manager, assigned_to=employee_two)
    start_timer(user=employee_one, task=first_task)
    stop_timer(user=employee_one, task=first_task)
    start_timer(user=employee_two, task=second_task)
    stop_timer(user=employee_two, task=second_task)

    client = APIClient()
    client.force_authenticate(user=manager)
    response = client.get(f"/api/reports/daily/?user_id={employee_one.id}")

    assert response.status_code == 200
    assert len(response.data["rows"]) == 1
    assert response.data["rows"][0]["user_name"] == employee_one.username


@pytest.mark.django_db
def test_weekly_csv_export_returns_attachment():
    employee = User.objects.create_user(
        username="weekly",
        email="weekly@example.com",
        password="strongpass123",
        role=User.Roles.EMPLOYEE,
    )
    task = Task.objects.create(title="Weekly task", description="x", created_by=employee, assigned_to=employee)
    start_timer(user=employee, task=task)
    stop_timer(user=employee, task=task)

    client = APIClient()
    client.force_authenticate(user=employee)
    response = client.get("/api/reports/weekly/export/")

    assert response.status_code == 200
    assert response["Content-Type"] == "text/csv"
    assert "attachment;" in response["Content-Disposition"]
