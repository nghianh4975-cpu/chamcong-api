from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from backend.database import get_db
from backend.models import User
from backend.schemas import Token, LoginRequest, UserCreate, UserResponse
from backend.auth import (
    verify_password, get_password_hash, create_access_token,
    get_current_user, get_client_ip
)
from backend.config import settings

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == login_data.username).first()
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tên đăng nhập hoặc mật khẩu không đúng"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị vô hiệu hóa"
        )

    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username, "role": user.role.value}
    )
    return {"access_token": access_token, "token_type": "bearer", "role": user.role.value}


@router.post("/login/form", response_model=Token)
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tên đăng nhập hoặc mật khẩu không đúng"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị vô hiệu hóa"
        )

    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username, "role": user.role.value}
    )
    return {"access_token": access_token, "token_type": "bearer", "role": user.role.value}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tên đăng nhập đã tồn tại"
        )

    hashed_pw = get_password_hash(user_data.password)
    user = User(
        username=user_data.username,
        password_hash=hashed_pw,
        role=user_data.role,
        employee_id=user_data.employee_id
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
