from enum import Enum


class Tags(Enum):
    """Enumeration of API route tags for documentation and organization.

    These tags are used to categorize and group API endpoints in the
    OpenAPI/Swagger documentation.
    They help in organizing and understanding the different sections of the API.

    Attributes:
        general (str): Tag for general or miscellaneous endpoints.
        api (str): Tag for core API-related endpoints.
        users (str): Tag for user-related endpoints.
        auth (str): Tag for authentication-related endpoints.
    """

    general = "General"
    api = "API"
    users = "Users"
    auth = "Authentication"
