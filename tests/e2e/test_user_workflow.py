import pytest
from fastapi.testclient import TestClient
from pyback.main import app


@pytest.fixture
def user_data():
    """Data for creating a test user."""
    return {
        "email": "testuser@example.com",
        "password": "testpassword123",
        "first_name": "Test",
        "last_name": "User",
    }


@pytest.fixture
def updated_user_data():
    """Data for updating a test user."""
    return {
        "first_name": "Updated",
        "last_name": "Name",
        "email": "updated@example.com",
    }


@pytest.fixture
def another_user_data():
    """Data for creating a second test user."""
    return {
        "email": "another@example.com",
        "password": "anotherpass123",
        "first_name": "Another",
        "last_name": "User",
    }


@pytest.fixture
def admin_credentials():
    """Admin user credentials for authentication."""
    return {
        "email": "admin@example.com",
        "password": "adminpass123",
    }


@pytest.fixture
def auth_headers(admin_credentials):
    """Get authentication headers with valid JWT token for an admin user."""
    with TestClient(app) as client:
        # Get JWT token
        token_response = client.post(
            "/auth/token",
            json=admin_credentials,
        )
        assert token_response.status_code == 200
        token = token_response.json()["access_token"]

        # Verify the user is an admin
        headers = {"Authorization": f"Bearer {token}"}
        user_response = client.get("/users/me", headers=headers)
        assert user_response.status_code == 200
        user_data = user_response.json()
        assert user_data["is_admin"] == True

        return headers


class TestUserEndpoints:
    def test_get_user_by_id(self, client, auth_headers, another_user_data):
        """Checks retrieval of a specific user by ID for authenticated admin."""
        # Create another user
        response = client.post("/users/", json=another_user_data, headers=auth_headers)
        assert response.status_code == 201

        # Get all users
        users_response = client.get("/users/", headers=auth_headers)
        users = users_response.json()
        another_users_list = [
            *filter(lambda user: user["email"] == another_user_data["email"], users)
        ]
        user_id = another_users_list[0]["id"]

        # Get specific user
        response = client.get(f"/users/{user_id}", headers=auth_headers)
        assert response.status_code == 200
        user = response.json()
        assert user["id"] == user_id

    def test_update_user(
        self, client, auth_headers, another_user_data, updated_user_data
    ):
        """Validates user information update process by authenticated admin."""
        # Create another user
        response = client.post("/users/", json=another_user_data, headers=auth_headers)
        assert response.status_code == 201

        # Get all users
        users_response = client.get("/users/", headers=auth_headers)
        users = users_response.json()
        another_users_list = [
            *filter(lambda user: user["email"] == another_user_data["email"], users)
        ]
        user_id = another_users_list[0]["id"]

        # Update user
        response = client.put(
            f"/users/{user_id}", json=updated_user_data, headers=auth_headers
        )
        assert response.status_code == 200
        updated_user = response.json()
        assert updated_user["first_name"] == updated_user_data["first_name"]
        assert updated_user["last_name"] == updated_user_data["last_name"]
        assert updated_user["email"] == another_user_data["email"]

    def test_delete_user(self, client, auth_headers, another_user_data):
        """Ensures proper soft deletion of a user by authenticated admin."""
        # Create another user
        response = client.post("/users/", json=another_user_data, headers=auth_headers)
        assert response.status_code == 201

        # Get all users
        users_response = client.get("/users/", headers=auth_headers)
        users = users_response.json()
        another_users_list = [
            *filter(lambda user: user["email"] == another_user_data["email"], users)
        ]
        user_id = another_users_list[0]["id"]

        # Delete user
        response = client.delete(f"/users/{user_id}", headers=auth_headers)
        assert response.status_code == 204

        # Try to get deleted user
        response = client.get(f"/users/{user_id}", headers=auth_headers)
        assert response.status_code == 404

    def test_reactivate_user(self, client, auth_headers, another_user_data):
        """Verifies reactivation of a soft-deleted user by authenticated admin."""
        # Create another user
        response = client.post("/users/", json=another_user_data, headers=auth_headers)
        assert response.status_code == 201

        # Get all users
        users_response = client.get("/users/", headers=auth_headers)
        users = users_response.json()
        another_users_list = [
            *filter(lambda user: user["email"] == another_user_data["email"], users)
        ]
        user_id = another_users_list[0]["id"]

        # Delete user
        client.delete(f"/users/{user_id}", headers=auth_headers)

        # Reactivate user
        response = client.post(f"/users/{user_id}/reactivate", headers=auth_headers)
        assert response.status_code == 204

        # Check if user is active again
        response = client.get(f"/users/{user_id}", headers=auth_headers)
        assert response.status_code == 200

    def test_non_admin_user_access(self, client, user_data):
        """Ensures non-admin users cannot perform admin-only actions."""
        # Create a non-admin user
        signup_response = client.post("/auth/signup", json=user_data)
        assert signup_response.status_code == 201

        # Get JWT token for non-admin user
        token_response = client.post(
            "/auth/token",
            json={
                "email": user_data["email"],
                "password": user_data["password"],
            },
        )
        assert token_response.status_code == 200
        token = token_response.json()["access_token"]
        non_admin_headers = {"Authorization": f"Bearer {token}"}

        # Try to perform admin-only actions
        response = client.get("/users/", headers=non_admin_headers)
        assert response.status_code == 403

        # Try to create a new user
        response = client.post("/users/", json=user_data, headers=non_admin_headers)
        assert response.status_code == 403

        # Try to delete a user
        response = client.delete(
            "/users/00000000-0000-0000-0000-000000000000", headers=non_admin_headers
        )
        assert response.status_code == 403
