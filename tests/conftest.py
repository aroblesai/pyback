import pytest
from pyback.api.dependencies.db import pgdb
from pyback.api.dependencies.db import redis_db
from fastapi.testclient import TestClient
from pyback.main import app
from .middleware import TestClientIPOverrideMiddleware

admin_user_data = {
    "email": "admin@example.com",
    "password": "adminpass123",
    "hashed_password": "$2b$12$fPKlXqsWsXHfDaHz90J90uRBdlzDwlEM2i92Z/Y.lD0WnXdbirCQa",
    "first_name": "Admin",
    "last_name": "User",
}


@pytest.fixture(autouse=True)
async def cleanup():
    yield
    await pgdb.connect()
    await pgdb.execute_with_transaction('TRUNCATE TABLE "users"')
    await pgdb.disconnect()
    await redis_db.connect()
    await redis_db.clean()  # Clear all rate limit data
    await redis_db.disconnect()


@pytest.fixture(autouse=True)
async def create_admin_user():

    await pgdb.connect()
    query = """DELETE FROM users WHERE email = :email;"""
    await pgdb.execute_with_transaction(
        query,
        parameters={
            "email": admin_user_data["email"],
        },
    )
    query = """INSERT INTO users(
        first_name, last_name, email, hashed_password, is_admin)
        VALUES (:first_name, :last_name, :email, :password, :is_admin);
        """
    await pgdb.execute_with_transaction(
        query,
        parameters={
            "first_name": admin_user_data["first_name"],
            "last_name": admin_user_data["last_name"],
            "email": admin_user_data["email"],
            "password": admin_user_data["hashed_password"],
            "is_admin": True,
        },
    )
    await pgdb.disconnect()
    yield


# Add the middleware to override client IP during tests
app.add_middleware(
    TestClientIPOverrideMiddleware, client_host="1.2.3.4", client_port=12345
)


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c
