import pytest
from rest_framework.test import APIClient

from tasks.models import Task

from .models import TimeEntry
from .services import ActiveTimerExistsError, start_timer


@pytest.fixture
def two_tasks(employee):
    first = Task.objects.create(title="Task 1", description="x", created_by=employee, assigned_to=employee)
    second = Task.objects.create(title="Task 2", description="y", created_by=employee, assigned_to=employee)
    return first, second


@pytest.mark.django_db
def test_only_one_active_timer_allowed(employee, two_tasks):
    first, second = two_tasks
    start_timer(user=employee, task=first)

    with pytest.raises(ActiveTimerExistsError):
        start_timer(user=employee, task=second)


@pytest.mark.django_db
def test_restarting_same_task_returns_existing_active_entry(employee, two_tasks):
    first, _ = two_tasks

    entry = start_timer(user=employee, task=first)
    repeated = start_timer(user=employee, task=first)

    assert repeated.id == entry.id
    assert TimeEntry.objects.filter(user=employee, end_time__isnull=True).count() == 1


@pytest.mark.django_db
def test_start_and_stop_timer_api(employee, two_tasks):
    first, _ = two_tasks
    client = APIClient()
    client.force_authenticate(user=employee)

    start_response = client.post(f"/api/time/start/{first.id}/")
    stop_response = client.post(f"/api/time/stop/{first.id}/")

    assert start_response.status_code == 201
    assert stop_response.status_code == 200
    entry = TimeEntry.objects.get(task=first, user=employee)
    assert entry.end_time is not None


@pytest.mark.django_db
def test_daily_report_contains_logged_task(employee, two_tasks):
    first, _ = two_tasks
    client = APIClient()
    client.force_authenticate(user=employee)

    client.post(f"/api/time/start/{first.id}/")
    client.post(f"/api/time/stop/{first.id}/")
    response = client.get("/api/reports/daily/")

    assert response.status_code == 200
    assert response.data["rows"][0]["task_title"] == "Task 1"
