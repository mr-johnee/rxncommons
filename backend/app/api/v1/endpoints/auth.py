from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
import hashlib

from app.api import deps
from app.crud import crud_user
from app.schemas.user import UserCreate, UserResponse, UserLogin
from app.schemas.token import Token, TokenRefreshRequest
from app.core.security import verify_password, create_access_token, generate_refresh_token_string
from app.core.config import settings
from app.models.system import AuthRefreshToken, SecurityAuditLog
from app.models.user import User

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(deps.get_db)):
    """
    用户注册接口
    """
    # 检查邮箱和用户名是否已存在
    if crud_user.get_user_by_email(db, email=user_in.email):
        raise HTTPException(
            status_code=400,
            detail="The user with this username or email already exists in the system",
        )
    if crud_user.get_user_by_username(db, username=user_in.username):
        raise HTTPException(
            status_code=400,
            detail="The user with this username or email already exists in the system",
        )
    
    # 创建用户
    user = crud_user.create_user(db, user=user_in)
    
    # 记录审计日志
    audit = SecurityAuditLog(user_id=user.id, event_type="register", details="New user registered")
    db.add(audit)
    db.commit()
    
    return user

@router.post("/login", response_model=Token)
def login(request: Request, user_in: UserLogin, db: Session = Depends(deps.get_db)):
    """
    用户登录接口，返回 Access Token 和 Refresh Token
    """
    client_ip = request.client.host if request.client else None
    user = crud_user.get_user_by_email(db, email=user_in.email)
    if not user or not verify_password(user_in.password, user.password_hash):
        # 记录登录失败审计日志
        audit = SecurityAuditLog(event_type="login_failed", ip_address=client_ip, details=f"Failed login attempt for email: {user_in.email}")
        db.add(audit)
        db.commit()
        raise HTTPException(
            status_code=401,
            detail="auth_invalid_credentials", # 对应设计文档中的系统错误规范
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 记录最后登录时间与审计日志
    user.last_login = datetime.utcnow()
    db.add(SecurityAuditLog(user_id=user.id, event_type="login_success", ip_address=client_ip))

    # 生成 Token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(subject=user.id, expires_delta=access_token_expires)
    
    # 生成并存储 Refresh Token (Hash)
    refresh_token = generate_refresh_token_string()
    refresh_token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    db_refresh_token = AuthRefreshToken(
        user_id=user.id,
        token_hash=refresh_token_hash,
        expires_at=expires_at,
        user_agent=request.headers.get("user-agent", "")[:500]
    )
    db.add(db_refresh_token)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/refresh", response_model=Token)
def refresh_token(request: Request, refresh_request: TokenRefreshRequest, db: Session = Depends(deps.get_db)):
    """
    使用 Refresh Token 换取新的 Access Token 和新的 Refresh Token（轮换机制）
    """
    refresh_token = refresh_request.refresh_token
    token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    
    # 查找数据库中这个 refresh token
    db_token = db.query(AuthRefreshToken).filter(AuthRefreshToken.token_hash == token_hash).first()
    
    if not db_token:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    if db_token.is_revoked:
        raise HTTPException(status_code=401, detail="Refresh token has been revoked")
        
    if db_token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Refresh token expired")

    # 查找到对应的用户
    user = db.query(User).filter(User.id == db_token.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
        
    # 执行轮换：使旧的 Refresh Token 作废
    db_token.is_revoked = True
    db.commit()

    # 重新生成 Access Token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(subject=user.id, expires_delta=access_token_expires)
    
    # 生成新的 Refresh Token 并入库记录
    new_refresh_token = generate_refresh_token_string()
    new_refresh_token_hash = hashlib.sha256(new_refresh_token.encode()).hexdigest()
    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    new_db_token = AuthRefreshToken(
        user_id=user.id,
        token_hash=new_refresh_token_hash,
        expires_at=expires_at,
        user_agent=request.headers.get("user-agent", "")[:500]
    )
    db.add(new_db_token)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/logout")
def logout(current_user: User = Depends(deps.get_current_active_user), db: Session = Depends(deps.get_db)):
    """
    用户登出，撤销该用户下所有的 Refresh Token
    """
    db.query(AuthRefreshToken).filter(AuthRefreshToken.user_id == current_user.id).update({"is_revoked": True})
    db.commit()
    
    # 记录审计日志
    audit = SecurityAuditLog(user_id=current_user.id, event_type="logout", details="User logged out manually")
    db.add(audit)
    db.commit()
    
    return {"detail": "Successfully logged out"}
from pydantic import EmailStr, BaseModel

class ForgotPasswordReq(BaseModel):
    email: EmailStr

class ResetPasswordReq(BaseModel):
    token: str
    new_password: str

@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordReq, db: Session = Depends(deps.get_db)):
    # Always return success to prevent user enumeration
    pass
    return {"status": "success", "message": "If the email is registered, a reset link has been sent."}

@router.post("/reset-password")
def reset_password(req: ResetPasswordReq, db: Session = Depends(deps.get_db)):
    # In real world, verify the token and extract user
    # For now, we mock success
    return {"status": "success", "message": "Password has been reset."}

@router.post("/verify-email")
def verify_email(token: str, db: Session = Depends(deps.get_db)):
    # Mock verify
    return {"status": "success", "message": "Email verified successfully."}
