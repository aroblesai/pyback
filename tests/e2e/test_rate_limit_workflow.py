import pytest


@pytest.fixture
def user_data():
    """User data for creating a new user."""
    return {
        "email": "testuser@example.com",
        "password": "testpassword123",
        "first_name": "Test",
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
def auth_headers(client, user_data):
    """Get authentication headers with valid JWT token for an admin user."""
    # Create a new user
    client.post("/auth/signup", json=user_data)

    # Get JWT token
    token_response = client.post(
        "/auth/token",
        json={"email": user_data["email"], "password": user_data["password"]},
    )
    assert token_response.status_code == 200
    token = token_response.json()["access_token"]

    # Verify the user is an admin
    headers = {"Authorization": f"Bearer {token}"}
    return headers


@pytest.fixture
def admin_auth_headers(client, admin_credentials):
    """Get authentication headers with valid JWT token for an admin user."""
    # Get JWT token
    token_response = client.post(
        "/auth/token",
        json=admin_credentials,
    )
    assert token_response.status_code == 200
    token = token_response.json()["access_token"]

    # Verify the user is an admin
    headers = {"Authorization": f"Bearer {token}"}
    return headers


class TestRateLimiter:
    def test_authenticated_rate_limit(self, client, auth_headers: dict[str, str]):
        """Test rate limiting for authenticated endpoints."""

        # Test default authenticated rate limit (100 requests per 60 seconds)
        for _ in range(100):
            response = client.get("/users/me", headers=auth_headers)
            assert response.status_code == 200

        # The 101st request should be rate limited
        response = client.get("/users/me", headers=auth_headers)
        assert response.status_code == 429
        assert "Too Many Requests" in response.text

    def test_admin_rate_limit(self, client, admin_auth_headers: dict[str, str]):
        """Test rate limiting for admin endpoints."""
        # Test admin rate limit (1000 requests per 60 seconds)
        for _ in range(1000):
            response = client.get("/users", headers=admin_auth_headers)
            assert response.status_code == 200

        # The 1001st request should be rate limited
        response = client.get("/users", headers=admin_auth_headers)
        assert response.status_code == 429
        assert "Too Many Requests" in response.text
