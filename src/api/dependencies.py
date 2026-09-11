import hashlib
from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.session import get_db
from src.infrastructure.database.models import User, UserRole
from src.infrastructure.database.repositories.user_repo import UserRepository

security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Deterministic secure hash for MVP"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Returns authenticated user or default system owner for easy testing"""
    user_repo = UserRepository(db)
    
    # Check if a user ID or token is passed
    if credentials and credentials.credentials:
        token = credentials.credentials
        # Check if token is user email or ID
        user = await user_repo.get_by_email(token)
        if not user:
            user = await user_repo.get_by_id(token)
        if user:
            return user

    # Default to Seed Owner for seamless local API exploration
    owner = await user_repo.get_by_id("00000000-0000-0000-0000-000000000001")
    if not owner:
        # Create default owner in db session if missing
        owner = User(
            id="00000000-0000-0000-0000-000000000001",
            email="owner@company.ai",
            password_hash=hash_password("owner123"),
            full_name="Company Owner",
            role=UserRole.OWNER,
        )
        owner = await user_repo.create(owner)
    return owner
