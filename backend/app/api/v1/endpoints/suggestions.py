from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from pydantic import BaseModel
from app.api import deps
from app.models.user import User
from app.models.interaction import AdminSuggestion

router = APIRouter()

class SuggestionStatusUpdate(BaseModel):
    status: str

@router.put("/{suggestion_id}/status")
def update_suggestion_status(
    suggestion_id: UUID,
    payload: SuggestionStatusUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    if payload.status not in ["resolved", "dismissed"]:
        raise HTTPException(status_code=422, detail="Invalid status")
        
    suggestion = db.query(AdminSuggestion).filter(AdminSuggestion.id == suggestion_id).first()
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
        
    if suggestion.recipient_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    suggestion.status = payload.status
    db.commit()
    return {"status": "success", "new_status": suggestion.status}

