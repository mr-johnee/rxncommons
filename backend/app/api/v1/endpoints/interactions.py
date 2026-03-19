from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.api import deps
from app.crud import crud_interaction, crud_dataset
from app.schemas.interaction import UpvoteResponse, DiscussionCreate, DiscussionResponse
from app.models.user import User
from app.core.dataset_access import evaluate_dataset_access

router = APIRouter()


def _ensure_dataset_readable(
    db: Session,
    dataset_id: UUID,
    current_user: User | None,
    dataset_access_token: str | None,
):
    dataset = crud_dataset.get_dataset(db, dataset_id)
    allowed, password_required = evaluate_dataset_access(
        db=db,
        dataset=dataset,
        current_user=current_user,
        access_token=dataset_access_token,
    )
    if not allowed:
        if password_required:
            raise HTTPException(status_code=403, detail={"code": "dataset_access_password_required"})
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset

@router.post("/{dataset_id}/upvote", response_model=UpvoteResponse)
def toggle_upvote(
    dataset_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    dataset_access_token: str | None = Header(default=None, alias="X-Dataset-Access-Token"),
):
    if not current_user.is_email_verified:
        raise HTTPException(status_code=403, detail="Email not verified")
        
    _ensure_dataset_readable(db, dataset_id, current_user, dataset_access_token)

    new_count, is_upvoted = crud_interaction.toggle_upvote(db, dataset_id=dataset_id, user_id=current_user.id)
    return {"dataset_id": dataset_id, "upvote_count": new_count, "is_upvoted": is_upvoted}


@router.get("/{dataset_id}/upvote-status")
def get_upvote_status(
    dataset_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User | None = Depends(deps.get_current_user_optional),
    dataset_access_token: str | None = Header(default=None, alias="X-Dataset-Access-Token"),
):
    _ensure_dataset_readable(db, dataset_id, current_user, dataset_access_token)
    if not current_user:
        return {"is_upvoted": False}
    return {"is_upvoted": crud_interaction.check_upvoted(db, dataset_id=dataset_id, user_id=current_user.id)}


@router.post("/{dataset_id}/view")
def record_view(
    dataset_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User | None = Depends(deps.get_current_user_optional),
    dataset_access_token: str | None = Header(default=None, alias="X-Dataset-Access-Token"),
):
    dataset = _ensure_dataset_readable(db, dataset_id, current_user, dataset_access_token)

    dataset.view_count = int(dataset.view_count or 0) + 1
    db.commit()
    db.refresh(dataset)
    return {"dataset_id": dataset_id, "view_count": dataset.view_count}

@router.post("/{dataset_id}/discussions", response_model=DiscussionResponse)
def create_discussion(
    dataset_id: UUID,
    discussion_in: DiscussionCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    dataset_access_token: str | None = Header(default=None, alias="X-Dataset-Access-Token"),
):
    if not current_user.is_email_verified:
        raise HTTPException(status_code=403, detail="Email not verified")
        
    _ensure_dataset_readable(db, dataset_id, current_user, dataset_access_token)

    discussion = crud_interaction.create_discussion(
        db=db,
        dataset_id=dataset_id,
        user_id=current_user.id,
        content=discussion_in.content,
        parent_id=discussion_in.parent_id,
        root_id=discussion_in.root_id
    )
    return discussion

@router.get("/{dataset_id}/discussions", response_model=List[DiscussionResponse])
def get_discussions(
    dataset_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User | None = Depends(deps.get_current_user_optional),
    dataset_access_token: str | None = Header(default=None, alias="X-Dataset-Access-Token"),
):
    _ensure_dataset_readable(db, dataset_id, current_user, dataset_access_token)
        
    discussions = crud_interaction.get_discussions(db, dataset_id)
    return discussions


@router.delete("/{dataset_id}/upvote")
def remove_upvote(
    dataset_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    dataset_access_token: str | None = Header(default=None, alias="X-Dataset-Access-Token"),
):
    dataset = _ensure_dataset_readable(db, dataset_id, current_user, dataset_access_token)
    
    from app.models.interaction import Upvote
    existing = db.query(Upvote).filter(Upvote.dataset_id==dataset_id, Upvote.user_id==current_user.id).first()
    if existing:
        db.delete(existing)
        dataset.upvote_count = max(dataset.upvote_count - 1, 0)
        db.commit()
        db.refresh(dataset)
    
    return {"dataset_id": dataset_id, "upvote_count": dataset.upvote_count}

@router.put("/{dataset_id}/discussions/{discussion_id}", response_model=DiscussionResponse)
def update_discussion(
    dataset_id: UUID,
    discussion_id: UUID,
    discussion_in: DiscussionCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    dataset_access_token: str | None = Header(default=None, alias="X-Dataset-Access-Token"),
):
    _ensure_dataset_readable(db, dataset_id, current_user, dataset_access_token)
    from app.models.interaction import Discussion
    discussion = db.query(Discussion).filter(Discussion.id == discussion_id, Discussion.dataset_id == dataset_id).first()
    if not discussion:
        raise HTTPException(status_code=404, detail="Discussion not found")
        
    if discussion.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this discussion")
        
    if discussion.deleted_at is not None:
        raise HTTPException(status_code=400, detail="Cannot edit a deleted discussion")
        
    discussion.content = discussion_in.content
    db.commit()
    db.refresh(discussion)
    return discussion

@router.delete("/{dataset_id}/discussions/{discussion_id}")
def delete_discussion(
    dataset_id: UUID,
    discussion_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    dataset_access_token: str | None = Header(default=None, alias="X-Dataset-Access-Token"),
):
    _ensure_dataset_readable(db, dataset_id, current_user, dataset_access_token)
    from app.models.interaction import Discussion
    from datetime import datetime
    discussion = db.query(Discussion).filter(Discussion.id == discussion_id, Discussion.dataset_id == dataset_id).first()
    if not discussion:
        raise HTTPException(status_code=404, detail="Discussion not found")
        
    if discussion.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this discussion")
        
    discussion.deleted_at = datetime.utcnow()
    discussion.deleted_by = current_user.id
    db.commit()
    return {"status": "success", "message": "Discussion deleted"}
