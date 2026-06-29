from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.auth_service import get_current_user

bearer_scheme = HTTPBearer()


async def require_auth(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    return await get_current_user(credentials.credentials)


async def require_senior(current_user: dict = Depends(require_auth)) -> dict:
    if current_user.get("role") not in ("senior_analyst", "manager"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return current_user
