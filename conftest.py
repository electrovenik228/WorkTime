import pytest

from tasks.models import Task
from users.models import User


@pytest.fixture
def employee(db):
    return User.objects.create_user(
        username="employee",
        email="employee@example.com",
        password="strongpass123",
        role=User.Roles.EMPLOYEE,
    )


@pytest.fixture
def manager(db):
    return User.objects.create_user(
        username="manager",
        email="manager@example.com",
        password="strongpass123",
        role=User.Roles.MANAGER,
    )


@pytest.fixture
def task(employee):
    return Task.objects.create(
        title="Test Task",
        description="desc",
        created_by=employee,
        assigned_to=employee,
    )
