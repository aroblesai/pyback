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


class TestRateLimiter:
    def test_public_login_rate_limit(self, client, user_data):
        """Test rate limiting for login endpoint (5 requests per 60 seconds)."""
        login_data = {"email": user_data["email"], "password": user_data["password"]}

        # First 5 requests should go through (even if they return 401)
        for _ in range(5):
            response = client.post("/auth/token", json=login_data)
            assert response.status_code == 401  # Invalid credentials

        # The 6th request should be rate limited
        response = client.post("/auth/token", json=login_data)
        assert response.status_code == 429
        assert "Too Many Requests" in response.text

    def test_public_signup_rate_limit(self, client, user_data):
        """Test rate limiting for signup endpoint (3 requests per 300 seconds)."""
        # First 3 requests should go through
        for _ in range(3):
            response = client.post("/auth/signup", json=user_data)
            assert response.status_code in (201, 409)  # Created or Conflict

        # The 4th request should be rate limited
        response = client.post("/auth/signup", json=user_data)
        assert response.status_code == 429
        assert "Too Many Requests" in response.text

    def test_different_clients_rate_limit(self, client):
        """Test that rate limits are applied per client."""
        login_data = {"email": "test@example.com", "password": "wrongpassword"}

        # Simulate different client IPs
        headers_1 = {"X-Forwarded-For": "1.1.1.1"}
        headers_2 = {"X-Forwarded-For": "2.2.2.2"}

        # First client makes 5 requests
        for _ in range(5):
            response = client.post("/auth/token", json=login_data, headers=headers_1)
            assert response.status_code == 401

        # First client should be rate limited
        response = client.post("/auth/token", json=login_data, headers=headers_1)
        assert response.status_code == 429

        # Second client should still be able to make requests
        for _ in range(5):
            response = client.post("/auth/token", json=login_data, headers=headers_2)
            assert response.status_code == 401
