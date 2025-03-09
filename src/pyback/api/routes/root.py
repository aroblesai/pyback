from fastapi import APIRouter, Depends
from loguru import logger
from pydantic import BaseModel

from pyback.api.dependencies.auth import admin_required, get_current_user
from pyback.api.models.common import Tags
from pyback.api.models.user import User
from pyback.core.utils import add


router = APIRouter()


@router.get("/")
async def root_endpoint():
    """Root endpoint."""
    return {"message": "Welcome to the API!"}


@router.get("/protected", tags=[Tags.api])
async def protected_route(current_user: User = Depends(get_current_user)):
    """Access a route that requires user authentication.

    This endpoint demonstrates a protected route that can only be accessed
    by authenticated users. It returns a personalized greeting using the
    current user's first name.

    Args:
        current_user (User): The authenticated user, automatically injected
        by the get_current_user dependency.

    Returns:
        dict: A greeting message personalized with the user's first name.
    """
    return {
        "message": f"Hello {current_user.first_name}, this is a protected route!",
    }


@router.get("/admin", tags=[Tags.api], dependencies=[Depends(admin_required)])
async def protected_admin_route():
    """Access a route that requires administrative privileges.

    This endpoint demonstrates a route that can only be accessed by users
    with administrative rights. It returns a generic admin route message.

    Returns:
        dict: A message indicating access to the admin route.
    """
    return {"message": "Hello, this is a protected admin route!"}


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    logger.info("Health check endpoint called")
    return {"status": "ok"}


class AddRequest(BaseModel):
    """Add request model."""

    x: int
    y: int


@router.post("/add")
def add_endpoint(request: AddRequest):
    """Add endpoint."""
    result = add(request.x, request.y)
    logger.info(f"Add operation {request.x} + {request.y} result: {result}")
    return {"result": result}
