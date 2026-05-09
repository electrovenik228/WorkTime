import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from .models import User


@pytest.mark.django_db
def test_register_returns_jwt_tokens():
    client = APIClient()

    response = client.post(
        "/api/register/",
        {
            "username": "alice",
            "email": "alice@example.com",
            "password": "strongpass123",
            "role": User.Roles.EMPLOYEE,
        },
        format="json",
    )

    assert response.status_code == 201
    assert "access" in response.data
    assert "refresh" in response.data
    assert response.data["user"]["username"] == "alice"


@pytest.mark.django_db
def test_logout_post_redirects_to_login(client):
    user = User.objects.create_user(
        username="bob",
        email="bob@example.com",
        password="strongpass123",
        role=User.Roles.EMPLOYEE,
    )
    client.force_login(user)

    response = client.post(reverse("logout"))

    assert response.status_code == 302
    assert response.url == reverse("login")


@pytest.mark.django_db
def test_logout_get_not_allowed(client):
    user = User.objects.create_user(
        username="carol",
        email="carol@example.com",
        password="strongpass123",
        role=User.Roles.EMPLOYEE,
    )
    client.force_login(user)

    response = client.get(reverse("logout"))

    assert response.status_code == 405
