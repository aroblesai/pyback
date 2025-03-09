import pytest


@pytest.fixture
def valid_user_signup_data():
    """Valid user data for signup."""
    return {
        "email": "test@example.com",
        "password": "testpassword",
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


class TestAuthentication:
    def test_user_signup_duplicate_email(self, client, valid_user_signup_data):
        """Ensures duplicate email registration is prevented."""
        # Create the user for the first time
        client.post("/auth/signup", json=valid_user_signup_data)

        # Try to create the user again with the same email
        response = client.post("/auth/signup", json=valid_user_signup_data)

        assert response.status_code == 409
        assert "email already exists" in response.json()["detail"].lower()

    def test_user_login(self, client, valid_user_signup_data):
        """Validates successful user login process."""
        client.post("/auth/signup", json=valid_user_signup_data)

        # Now, try to login
        response = client.post(
            "/auth/token",
            json={
                "email": valid_user_signup_data["email"],
                "password": valid_user_signup_data["password"],
            },
        )

        assert response.status_code == 200
        token_data = response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"

    def test_protected_route(self, client, valid_user_signup_data):
        """Verifies access to protected routes with valid credentials."""
        # First, register user
        client.post("/auth/signup", json=valid_user_signup_data)

        login_response = client.post(
            "/auth/token",
            json={
                "email": valid_user_signup_data["email"],
                "password": valid_user_signup_data["password"],
            },
        )
        token = login_response.json()["access_token"]

        # Now, try to access a protected route
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/protected", headers=headers)

        assert response.status_code == 200
        user_info = response.json()
        assert valid_user_signup_data["first_name"] in user_info["message"]

    def test_no_access_admin_route(self, client, valid_user_signup_data):
        """Verifies access to admin routes with valid credentials."""
        # First, register user
        client.post("/auth/signup", json=valid_user_signup_data)

        login_response = client.post(
            "/auth/token",
            json={
                "email": valid_user_signup_data["email"],
                "password": valid_user_signup_data["password"],
            },
        )
        token = login_response.json()["access_token"]

        # Now, try to access a admin route
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/admin", headers=headers)

        assert response.status_code == 403
        assert "permission denied" in response.json()["detail"].lower()

    def test_access_admin_route(self, client, admin_credentials):
        """Verifies access to admin routes with valid credentials."""
        login_response = client.post(
            "/auth/token",
            json=admin_credentials,
        )
        token = login_response.json()["access_token"]

        # Now, try to access a admin route
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/admin", headers=headers)

        assert response.status_code == 200
        assert "protected admin route" in response.json()["message"].lower()
