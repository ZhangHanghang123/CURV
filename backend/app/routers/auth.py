"""登录认证"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import SysUser
from ..schemas import ResponseBase
from ..dependencies import (
    verify_password,
    create_access_token,
    get_current_user,
)

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/login", response_model=ResponseBase)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """OAuth2 form 登录"""
    user = (
        db.query(SysUser)
        .filter(SysUser.username == form_data.username, SysUser.is_deleted == 0)
        .first()
    )
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")

    if user.status != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="用户已禁用")

    user.last_login_at = datetime.now()
    db.commit()

    token = create_access_token({"sub": str(user.id), "username": user.username})

    return ResponseBase(
        data={
            "token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "real_name": user.real_name,
                "is_admin": bool(user.is_admin),
                "roles": [r.role_code for r in user.roles],
            },
        }
    )


@router.get("/me", response_model=ResponseBase)
def get_me(current_user: dict = Depends(get_current_user)):
    return ResponseBase(data=current_user)


@router.post("/logout", response_model=ResponseBase)
def logout(current_user: dict = Depends(get_current_user)):
    return ResponseBase(message="已登出")