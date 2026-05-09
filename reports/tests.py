import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from tasks.models import Task
from tracking.models import TimeEntry
from tracking.services import start_timer, stop_timer

from .services import build_daily_report, build_weekly_report


def _make_entry(user, task, minutes):
    now = timezone.now()
    return TimeEntry.objects.create(
        user=user,
        task=task,
        start_time=now - timezone.timedelta(minutes=minutes),
        end_time=now,
    )


# --- build_daily_report ---

@pytest.mark.django_db
def test_daily_report_sums_duration_for_task(employee, task):
    _make_entry(employee, task, minutes=30)
    _make_entry(employee, task, minutes=15)

    report = build_daily_report(employee)

    assert len(report["rows"]) == 1
    assert report["rows"][0]["task_title"] == "Test Task"
    assert report["rows"][0]["seconds"] >= 45 * 60


@pytest.mark.django_db
def test_daily_report_empty_when_no_entries(employee):
    report = build_daily_report(employee)

    assert report["rows"] == []


@pytest.mark.django_db
def test_daily_report_employee_sees_only_own_entries(employee, manager):
    manager_task = Task.objects.create(
        title="Manager Task", description="", created_by=manager, assigned_to=manager
    )
    employee_task = Task.objects.create(
        title="My Task", description="", created_by=employee, assigned_to=employee
    )
    _make_entry(manager, manager_task, minutes=60)
    _make_entry(employee, employee_task, minutes=30)

    report = build_daily_report(employee)

    usernames = {row["user_name"] for row in report["rows"]}
    assert usernames == {"employee"}


@pytest.mark.django_db
def test_daily_report_manager_sees_all_entries(employee, manager, task):
    _make_entry(employee, task, minutes=30)

    report = build_daily_report(manager)

    assert any(row["user_name"] == "employee" for row in report["rows"])


@pytest.mark.django_db
def test_daily_report_manager_filtered_by_user(employee, manager, task):
    manager_task = Task.objects.create(
        title="Manager Task", description="", created_by=manager, assigned_to=manager
    )
    _make_entry(employee, task, minutes=30)
    _make_entry(manager, manager_task, minutes=60)

    report = build_daily_report(manager, target_user=employee)

    usernames = {row["user_name"] for row in report["rows"]}
    assert usernames == {"employee"}


# --- build_weekly_report ---

@pytest.mark.django_db
def test_weekly_report_has_seven_days(employee, task):
    _make_entry(employee, task, minutes=60)

    report = build_weekly_report(employee)

    assert len(report["days"]) == 7
    assert report["week_start"] <= report["week_end"]


@pytest.mark.django_db
def test_weekly_report_total_covers_entry(employee, task):
    _make_entry(employee, task, minutes=60)

    report = build_weekly_report(employee)

    assert report["total_seconds"] >= 60 * 60


@pytest.mark.django_db
def test_weekly_report_single_day_is_100_percent(employee, task):
    _make_entry(employee, task, minutes=60)

    report = build_weekly_report(employee)

    non_zero = [d for d in report["days"] if d["seconds"] > 0]
    assert len(non_zero) == 1
    assert non_zero[0]["percent"] == 100


@pytest.mark.django_db
def test_weekly_report_empty_has_zero_total(employee):
    report = build_weekly_report(employee)

    assert report["total_seconds"] == 0
    assert all(d["seconds"] == 0 for d in report["days"])


# --- API endpoints ---

@pytest.mark.django_db
def test_daily_report_api(employee, task):
    _make_entry(employee, task, minutes=20)
    client = APIClient()
    client.force_authenticate(user=employee)

    response = client.get("/api/reports/daily/")

    assert response.status_code == 200
    assert response.data["rows"][0]["task_title"] == "Test Task"


@pytest.mark.django_db
def test_daily_csv_export(employee, task):
    _make_entry(employee, task, minutes=20)
    client = APIClient()
    client.force_authenticate(user=employee)

    response = client.get("/api/reports/daily/export/")

    assert response.status_code == 200
    assert response["Content-Type"] == "text/csv"
    assert "attachment;" in response["Content-Disposition"]
    assert b"Test Task" in response.content


@pytest.mark.django_db
def test_weekly_csv_export(employee, task):
    _make_entry(employee, task, minutes=20)
    client = APIClient()
    client.force_authenticate(user=employee)

    response = client.get("/api/reports/weekly/export/")

    assert response.status_code == 200
    assert response["Content-Type"] == "text/csv"
    assert "attachment;" in response["Content-Disposition"]


@pytest.mark.django_db
def test_manager_can_filter_daily_report_by_user_id(employee, manager, task):
    manager_task = Task.objects.create(
        title="Manager Task", description="", created_by=manager, assigned_to=manager
    )
    start_timer(user=employee, task=task)
    stop_timer(user=employee, task=task)
    start_timer(user=manager, task=manager_task)
    stop_timer(user=manager, task=manager_task)
    client = APIClient()
    client.force_authenticate(user=manager)

    response = client.get(f"/api/reports/daily/?user_id={employee.id}")

    assert response.status_code == 200
    assert len(response.data["rows"]) == 1
    assert response.data["rows"][0]["user_name"] == "employee"
