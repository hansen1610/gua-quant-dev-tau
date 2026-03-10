"""
╔══════════════════════════════════════════════════════════════╗
║  Authentication Routes — JWT-based                           ║
║  Login, token verification, and auth dependencies            ║
╚══════════════════════════════════════════════════════════════╝
"""
import os
from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError
import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = structlog.get_logger()
router = APIRouter()

JWT_SECRET = os.getenv("JWT_SECRET_KEY", "change_me_jwt_secret_minimum_32_chars")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

security = HTTPBearer(auto_error=False)


@router.post("/login")
async def login(payload: dict, request: Request):
    """Authenticate user against PostgreSQL and issue a JWT."""
    username = payload.get("username", "")
    password = payload.get("password", "")

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password are required",
        )

    db = request.app.state.db_pool
    
    # Try database login first if DB is available
    if db:
        try:
            async with db.acquire() as conn:
                user = await conn.fetchrow(
                    """
                    SELECT id, username, role, is_active 
                    FROM users 
                    WHERE username = $1 
                      AND password_hash = crypt($2, password_hash)
                    """,
                    username,
                    password,
                )

                if user:
                    if not user["is_active"]:
                        raise HTTPException(status_code=403, detail="Account is deactivated")
                    
                    return _issue_token(user["id"], user["username"], user["role"])
        except Exception as e:
            logger.warning("auth.db_login_failed", error=str(e))

    # Fallback to hardcoded admin for UI review/dev
    admin_user = os.getenv("ADMIN_USERNAME", "admin")
    admin_pass = os.getenv("ADMIN_PASSWORD", "password")
    
    if username == admin_user and password == admin_pass:
        return _issue_token("infra-admin", admin_user, "admin")

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
    )

def _issue_token(user_id: str, username: str, role: str):
    now = datetime.now(timezone.utc)
    token_payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "iat": now,
        "exp": now + timedelta(hours=JWT_EXPIRATION_HOURS),
    }
    access_token = jwt.encode(token_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": role,
        "username": username,
    }


@router.get("/verify")
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT and return user info."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token required"
        )
    try:
        payload = jwt.decode(
            credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM]
        )
        return {
            "status": "authorized",
            "username": payload.get("username"),
            "role": payload.get("role"),
            "user_id": payload.get("sub"),
        }
    except JWTError as e:
        detail = "Token expired" if "expired" in str(e).lower() else "Invalid token"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=detail
        )


# ── Dependency for protecting routes ─────────────────────
async def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """FastAPI dependency to require valid JWT on protected routes."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    try:
        payload = jwt.decode(
            credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        detail = "Token expired" if "expired" in str(e).lower() else "Invalid token"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=detail
        )


async def require_admin(user: dict = Depends(require_auth)) -> dict:
    """Require admin role."""
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )
    return user
