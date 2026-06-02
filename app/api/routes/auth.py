from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.deps import get_db
from app.models.user import User
from app.schemas.api import LoginIn, TokenOut, UserCreate, UserOut

router = APIRouter()


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)) -> TokenOut:
    user = db.execute(select(User).where(User.email == payload.email)).scalars().first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid_credentials")
    token = create_access_token(user.email, {"uid": user.id, "role": user.role.value})
    return TokenOut(access_token=token)


@router.post("/users", response_model=UserOut)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> UserOut:
    exists = db.execute(select(User).where(User.email == payload.email)).scalars().first()
    if exists:
        raise HTTPException(status_code=409, detail="email_exists")
    user = User(
        email=payload.email,
        password_hash=get_password_hash(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(user)
