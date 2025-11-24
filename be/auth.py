import os
from datetime import datetime, timedelta
from typing import Optional

from authlib.jose import jwt
from authlib.jose.errors import JoseError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from models.tortoise import User
from models.enums import Role

SECRET_KEY = os.getenv("JWT_SECRET", "change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24))

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    
    to_encode.update({"exp": int(expire.timestamp())})
    header = {"alg": ALGORITHM}
    token = jwt.encode(header, to_encode, SECRET_KEY)
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token


async def get_user_by_id(user_id: int) -> Optional[User]:
    try:
        return await User.get(id=user_id)
    except Exception:
        return None


async def get_user_by_username(username: str) -> Optional[User]:
    try:
        return await User.get(username=username)
    except Exception:
        return None


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        claims = jwt.decode(token, SECRET_KEY)
        claims.validate()
        payload = dict(claims)
        user_id: int = payload.get("id")
        if user_id is None:
            raise credentials_exception
    except (JoseError, Exception):
        raise credentials_exception
    user = await get_user_by_id(user_id)
    if user is None:
        raise credentials_exception
    return user


async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    try:
        role = current_user.role
        if hasattr(role, "value"):
            is_admin = role == Role.ADMIN
        else:
            is_admin = str(role) == Role.ADMIN.value
    except Exception:
        is_admin = False
    if not is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Requires administrator role")
    return current_user


async def get_current_admin_or_head_user(current_user: User = Depends(get_current_user)) -> User:
    """Allows both Admin and Head of Department"""
    try:
        role = current_user.role
        if hasattr(role, "value"):
            is_authorized = role in (Role.ADMIN, Role.HEAD)
        else:
            is_authorized = str(role) in (Role.ADMIN.value, Role.HEAD.value)
    except Exception:
        is_authorized = False
    if not is_authorized:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Requires administrator or head of department role")
    return current_user
