from fastapi import APIRouter
from app.schemas.user import UserCreate, TokenResponse, LoginRequest, UserResponse
from app.services.auth_service import register_user, authenticate_user
from app.dependencies import require_auth
from fastapi import Depends

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=201)
async def register(user: UserCreate):
    return await register_user(user)


@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest):
    return await authenticate_user(credentials.username, credentials.password)


@router.get("/me", response_model=UserResponse)
async def me(current_user: dict = Depends(require_auth)):
    return current_user
