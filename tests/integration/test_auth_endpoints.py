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
def invalid_credentials():
    """Invalid user credentials for authentication."""
    return {
        "email": "nonexistent@example.com",
        "password": "wrongpassword",
    }


class TestAuthentication:
    @pytest.mark.parametrize(
        "invalid_email",
        [
            "notanemail",
            "missing@tld",
            "@nodomain.com",
            "spaces in@email.com",
            "multiple@@at.com",
            ".startwithdot@domain.com",
            "endwithdot.@domain.com",
            "",
            "a" * 256 + "@toolong.com",  # Test email length limit
        ],
    )
    def test_user_signup_invalid_email(
        self, client, valid_user_signup_data, invalid_email
    ):
        """Validates email format rejection during signup."""
        invalid_data = valid_user_signup_data.copy()
        invalid_data["email"] = invalid_email

        response = client.post("/auth/signup", json=invalid_data)

        assert response.status_code == 422
        response_fields = [d["loc"][-1] for d in response.json()["detail"]]
        assert "email" in response_fields

    @pytest.mark.parametrize(
        "invalid_password",
        [
            "",  # Empty password
            "short",  # Too short
            "a" * 129,  # Too long (assuming reasonable max length)
            " " * 10,  # Only spaces
            "\t\n\r",  # Only whitespace
        ],
    )
    def test_user_signup_invalid_password(
        self, client, valid_user_signup_data, invalid_password
    ):
        """Ensures invalid password formats are blocked during signup."""
        invalid_data = valid_user_signup_data.copy()
        invalid_data["password"] = invalid_password

        response = client.post("/auth/signup", json=invalid_data)

        assert response.status_code == 422
        response_fields = [d["loc"][-1] for d in response.json()["detail"]]
        assert "password" in response_fields

    @pytest.mark.parametrize(
        "field,invalid_value",
        [
            ("first_name", ""),  # Empty first name
            ("first_name", "a" * 256),  # Too long first name
            ("first_name", " "),  # Only space
            ("last_name", ""),  # Empty last name
            ("last_name", "a" * 256),  # Too long last name
            ("last_name", " "),  # Only space
        ],
    )
    def test_user_signup_invalid_names(
        self, client, valid_user_signup_data, field, invalid_value
    ):
        """Checks name validation during user signup."""
        invalid_data = valid_user_signup_data.copy()
        invalid_data[field] = invalid_value

        response = client.post("/auth/signup", json=invalid_data)

        assert response.status_code == 422
        response_fields = [d["loc"][-1] for d in response.json()["detail"]]
        assert field in response_fields

    def test_user_signup_success(self, client, valid_user_signup_data):
        """Verifies successful user registration process."""
        response = client.post("/auth/signup", json=valid_user_signup_data)
        assert response.status_code == 201
        created_user = response.json()

        assert created_user["email"] == valid_user_signup_data["email"]
        assert created_user["first_name"] == valid_user_signup_data["first_name"]
        assert created_user["last_name"] == valid_user_signup_data["last_name"]
        assert "id" in created_user
        assert "password" not in created_user
        assert "password_hashed" not in created_user

    def test_user_signup_malformed_json(self, client):
        """Validates rejection of malformed JSON during signup."""
        response = client.post(
            "/auth/signup",
            data="not a json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    def test_user_signup_wrong_content_type(self, client, valid_user_signup_data):
        """Ensures incorrect content type is rejected during signup."""
        response = client.post(
            "/auth/signup",
            data=str(valid_user_signup_data),
            headers={"Content-Type": "text/plain"},
        )
        assert response.status_code == 422

    def test_user_login_with_invalid_credentials(self, client, invalid_credentials):
        """Validates login failure with incorrect credentials."""
        response = client.post("/auth/token", json=invalid_credentials)

        assert response.status_code == 401
        assert "could not validate credentials" in response.json()["detail"].lower()

    @pytest.mark.parametrize(
        "missing_field", ["email", "password", "first_name", "last_name"]
    )
    def test_user_signup_missing_required_fields(
        self, client, valid_user_signup_data, missing_field
    ):
        """Checks signup rejection when required fields are missing."""
        invalid_data = valid_user_signup_data.copy()
        del invalid_data[missing_field]

        response = client.post("/auth/signup", json=invalid_data)

        assert response.status_code == 422

    @pytest.mark.parametrize(
        "invalid_token",
        [
            "",  # Empty token
            "not_a_bearer_token",  # Missing Bearer prefix
            "Bearer ",  # Empty token with Bearer prefix
            "Bearer invalid.token.format",  # Invalid JWT format
            "Bearer " + "a" * 1000,  # Too long token
        ],
    )
    def test_protected_route_invalid_token_formats(self, client, invalid_token):
        """Checks token validation for protected routes."""
        headers = {"Authorization": invalid_token}
        response = client.get("/protected", headers=headers)

        assert response.status_code == 401
        response_msg = response.json()["detail"].lower()
        assert (
            "missing authentication token" in response_msg
            or "not authenticated" in response_msg
        )

    @pytest.mark.parametrize(
        "invalid_token",
        [
            "",  # Empty token
            "not_a_bearer_token",  # Missing Bearer prefix
            "Bearer ",  # Empty token with Bearer prefix
            "Bearer invalid.token.format",  # Invalid JWT format
            "Bearer " + "a" * 1000,  # Too long token
        ],
    )
    def test_admin_route_invalid_token_formats(self, client, invalid_token):
        """Checks token validation for admin routses."""
        headers = {"Authorization": invalid_token}
        response = client.get("/admin", headers=headers)

        assert response.status_code == 401
        response_msg = response.json()["detail"].lower()
        assert (
            "missing authentication token" in response_msg
            or "not authenticated" in response_msg
        )
