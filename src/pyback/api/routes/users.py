from uuid import UUID

from fastapi import APIRouter, Depends

from pyback.api.dependencies.auth import admin_required, get_current_user
from pyback.api.dependencies.rate_limit import rate_limit
from pyback.api.dependencies.users import get_user_service
from pyback.api.models.user import User, UserCreate, UserUpdate
from pyback.config.rate_limit import RateLimitConfig
from pyback.core.exceptions import ConflictError, NotFoundError
from pyback.services.users import UserService


router = APIRouter(
    dependencies=[
        Depends(get_current_user),
        Depends(rate_limit(RateLimitConfig.Scope.ADMIN)),
    ],
)


@router.get("/", response_model=list[User], dependencies=[Depends(admin_required)])
async def get_active_users(
    users_service: UserService = Depends(get_user_service),
):
    """Retrieve all active users."""
    return await users_service.list_active_users()


@router.post(
    "/",
    response_model=User,
    status_code=201,
    dependencies=[Depends(admin_required)],
)
async def create_user(
    user: UserCreate,
    users_service: UserService = Depends(get_user_service),
):
    """Create a new user."""
    try:
        new_user = await users_service.create_user(user)
        return new_user
    except ValueError as e:
        raise ConflictError(str(e))


@router.get(
    "/me",
    response_model=User,
    dependencies=[Depends(rate_limit(RateLimitConfig.Scope.AUTHENTICATED))],
)
async def get_my_user_info(
    get_current_user=Depends(get_current_user),
):
    """Retrieve user information for the currently authenticated user."""
    return get_current_user


@router.get("/{user_id}", response_model=User, dependencies=[Depends(admin_required)])
async def get_user(
    user_id: UUID,
    users_service: UserService = Depends(get_user_service),
):
    """Retrieve a specific user by ID."""
    user = await users_service.get_user(user_id)
    if not user or not user.is_active:
        raise NotFoundError
    return user


@router.put("/{user_id}", response_model=User, dependencies=[Depends(admin_required)])
async def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    users_service: UserService = Depends(get_user_service),
):
    """Update a specific user by ID."""
    updated_user = await users_service.update_user(user_id, user_update)
    if not updated_user:
        raise NotFoundError
    return updated_user


@router.delete(
    "/{user_id}",
    response_model=None,
    status_code=204,
    dependencies=[Depends(admin_required)],
)
async def delete_user(
    user_id: UUID,
    users_service: UserService = Depends(get_user_service),
):
    """Soft delete a user."""
    user = await users_service.get_user(user_id)
    if not user:
        raise NotFoundError
    await users_service.delete_user(user_id)


@router.post(
    "/{user_id}/reactivate",
    response_model=None,
    status_code=204,
    dependencies=[Depends(admin_required)],
)
async def reactivate_user(
    user_id: UUID,
    users_service: UserService = Depends(get_user_service),
):
    """Reactivate a soft-deleted user."""
    user = await users_service.get_user(user_id)
    if not user:
        raise NotFoundError
    await users_service.reactivate_user(user_id)
