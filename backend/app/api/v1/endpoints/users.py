from fastapi import APIRouter, Depends
from app.api import deps
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter()

@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(deps.get_current_active_user)):
    """
    获取当前登录用户的信息
    """
    return current_user

from pydantic import BaseModel
class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str

from sqlalchemy.orm import Session
from app.core.security import verify_password, get_password_hash

@router.put("/me/password")
def update_password(
    payload: PasswordUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    if not verify_password(payload.current_password, current_user.hashed_password):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Incorrect password")
        
    current_user.hashed_password = get_password_hash(payload.new_password)
    db.commit()
    return {"status": "success", "message": "Password updated successfully"}
