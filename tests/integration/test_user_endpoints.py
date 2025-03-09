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
    def test_create_user(self, client, user_data, auth_headers):
        """Validates successful user creation by authenticated admin."""
        response = client.post("/users/", json=user_data, headers=auth_headers)
        assert response.status_code == 201
        created_user = response.json()
        assert created_user["email"] == user_data["email"]
        assert created_user["first_name"] == user_data["first_name"]
        assert created_user["last_name"] == user_data["last_name"]
        assert "id" in created_user
        assert "password" not in created_user
        assert "hashed_password" not in created_user

    def test_create_duplicate_user(self, client, user_data, auth_headers):
        """Ensures duplicate user creation is prevented by email uniqueness."""
        client.post("/users/", json=user_data, headers=auth_headers)
        response = client.post("/users/", json=user_data, headers=auth_headers)
        assert response.status_code == 409
        assert "email already exists" in response.json()["detail"].lower()

    def test_unauthorized_access(self, client, user_data):
        """Verifies that endpoints reject requests without authentication."""
        # Try to create user without auth
        response = client.post("/users/", json=user_data)
        assert response.status_code == 401

        # Try to get users without auth
        response = client.get("/users/")
        assert response.status_code == 401

        # Try to get specific user without auth
        response = client.get("/users/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 401

    def test_invalid_token_access(self, client):
        """Ensures endpoints reject requests with invalid tokens."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/users/", headers=headers)
        assert response.status_code == 401

    def test_get_active_users(self, client, auth_headers):
        """Verifies retrieval of all active users by authenticated admin."""
        response = client.get("/users/", headers=auth_headers)
        assert response.status_code == 200
        users = response.json()
        assert isinstance(users, list)
        assert len(users) > 0

    def test_get_nonexistent_user(self, client, auth_headers):
        """Checks handling of requests for non-existent users."""
        response = client.get(
            "/users/00000000-0000-0000-0000-000000000000", headers=auth_headers
        )
        assert response.status_code == 404

    def test_update_nonexistent_user(self, client, auth_headers, updated_user_data):
        """Validates error handling when updating a non-existent user."""
        response = client.put(
            "/users/00000000-0000-0000-0000-000000000000",
            json=updated_user_data,
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_delete_nonexistent_user(self, client, auth_headers):
        """Ensures proper handling when attempting to delete a non-existent user."""
        response = client.delete(
            "/users/00000000-0000-0000-0000-000000000000", headers=auth_headers
        )
        assert response.status_code == 404

    def test_reactivate_nonexistent_user(self, client, auth_headers):
        """Verifies error handling when reactivating a non-existent user."""
        response = client.post(
            "/users/00000000-0000-0000-0000-000000000000/reactivate",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_expired_token(self, client):
        """Verifies that expired tokens are rejected."""
        # Using an expired token format but with invalid signature
        expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiZXhwIjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        expired_headers = {"Authorization": f"Bearer {expired_token}"}

        response = client.get("/users/", headers=expired_headers)
        assert response.status_code == 401
        response_msg = response.json()["detail"].lower()
        assert "invalid" in response_msg and "token" in response_msg
