from sqlalchemy.orm import Session
from app.models.interaction import Upvote, Discussion
from app.models.dataset import Dataset
from uuid import UUID

def toggle_upvote(db: Session, dataset_id: UUID, user_id: UUID) -> tuple[int, bool]:
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        return 0, False

    existing_upvote = db.query(Upvote).filter(
        Upvote.dataset_id == dataset_id,
        Upvote.user_id == user_id
    ).first()

    if existing_upvote:
        db.delete(existing_upvote)
        dataset.upvote_count -= 1
        is_upvoted = False
    else:
        new_upvote = Upvote(dataset_id=dataset_id, user_id=user_id)
        db.add(new_upvote)
        dataset.upvote_count += 1
        is_upvoted = True

    db.commit()
    db.refresh(dataset)
    return dataset.upvote_count, is_upvoted

def check_upvoted(db: Session, dataset_id: UUID, user_id: UUID) -> bool:
    return db.query(Upvote).filter(
        Upvote.dataset_id == dataset_id,
        Upvote.user_id == user_id
    ).first() is not None

def create_discussion(db: Session, dataset_id: UUID, user_id: UUID, content: str, parent_id: UUID = None, root_id: UUID = None) -> Discussion:
    new_discussion = Discussion(
        dataset_id=dataset_id,
        user_id=user_id,
        content=content,
        parent_id=parent_id,
        root_id=root_id
    )
    db.add(new_discussion)
    db.commit()
    db.refresh(new_discussion)
    return new_discussion

def get_discussions(db: Session, dataset_id: UUID):
    return db.query(Discussion).filter(
        Discussion.dataset_id == dataset_id,
        Discussion.deleted_at.is_(None)
    ).order_by(Discussion.created_at.desc()).all()
