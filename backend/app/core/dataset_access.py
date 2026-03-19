from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable

from jose import JWTError, jwt
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.models.dataset import Dataset, DatasetVersion
from app.models.dataset_access import (
    ACCESS_LEVEL_PASSWORD_PROTECTED,
    ACCESS_LEVEL_PUBLIC,
    DatasetAccessPolicy,
)
from app.models.interaction import DatasetReviewRequest
from app.models.user import User

PUBLIC_VISIBLE_STATUSES = {"published"}
DATASET_ACCESS_TOKEN_TYPE = "dataset_access"
DATASET_ACCESS_TOKEN_TTL_HOURS = 12


def _build_dataset_access_token(dataset_id: str, expires_hours: int = DATASET_ACCESS_TOKEN_TTL_HOURS) -> str:
    expire = datetime.utcnow() + timedelta(hours=expires_hours)
    payload = {
        "sub": dataset_id,
        "exp": expire,
        "typ": DATASET_ACCESS_TOKEN_TYPE,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def create_dataset_access_token(dataset: Dataset) -> str:
    return _build_dataset_access_token(str(dataset.id))


def verify_dataset_access_token(dataset_id: str, token: str | None) -> bool:
    if not token:
        return False
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except JWTError:
        return False
    return (
        payload.get("typ") == DATASET_ACCESS_TOKEN_TYPE
        and str(payload.get("sub")) == str(dataset_id)
    )


def get_dataset_access_policy(db: Session, dataset_id) -> DatasetAccessPolicy | None:
    return db.query(DatasetAccessPolicy).filter(DatasetAccessPolicy.dataset_id == dataset_id).first()


def attach_access_level(dataset: Dataset, policy: DatasetAccessPolicy | None, include_password: bool = False) -> None:
    level = policy.access_level if policy else ACCESS_LEVEL_PUBLIC
    setattr(dataset, "access_level", level)
    setattr(dataset, "is_password_protected", level == ACCESS_LEVEL_PASSWORD_PROTECTED)
    if include_password and level == ACCESS_LEVEL_PASSWORD_PROTECTED and policy and policy.password_hash:
        # Avoid displaying actual hashes in frontend if they start with bcrypt marker
        if not policy.password_hash.startswith("$2b$"):
            setattr(dataset, "access_password", policy.password_hash)
        else:
            setattr(dataset, "access_password", None)
    else:
        setattr(dataset, "access_password", None)


def attach_access_levels(db: Session, datasets: Iterable[Dataset], include_password: bool = False) -> None:
    dataset_list = list(datasets)
    if not dataset_list:
        return
    dataset_ids = [d.id for d in dataset_list]
    rows = db.query(DatasetAccessPolicy).filter(DatasetAccessPolicy.dataset_id.in_(dataset_ids)).all()
    policy_map = {row.dataset_id: row for row in rows}
    for ds in dataset_list:
        attach_access_level(ds, policy_map.get(ds.id), include_password=include_password)


def dataset_has_published_version(db: Session, dataset_id) -> bool:
    return db.query(DatasetVersion.id).filter(
        DatasetVersion.dataset_id == dataset_id,
        DatasetVersion.status == "published",
    ).first() is not None


def dataset_has_approved_review(db: Session, dataset_id) -> bool:
    return db.query(DatasetReviewRequest.id).filter(
        DatasetReviewRequest.dataset_id == dataset_id,
        DatasetReviewRequest.status == "approved",
    ).first() is not None


def is_dataset_publicly_browsable(db: Session, dataset: Dataset | None) -> bool:
    if not dataset or dataset.deleted_at is not None:
        return False
    if dataset.dataset_status not in PUBLIC_VISIBLE_STATUSES:
        return False

    policy = get_dataset_access_policy(db, dataset.id)
    if policy and policy.access_level == ACCESS_LEVEL_PASSWORD_PROTECTED:
        return False

    return dataset_has_published_version(db, dataset.id) and dataset_has_approved_review(db, dataset.id)


def evaluate_dataset_access(
    *,
    db: Session,
    dataset: Dataset | None,
    current_user: User | None,
    access_token: str | None,
) -> tuple[bool, bool]:
    """
    Returns (allowed, password_required).
    """
    if not dataset or dataset.deleted_at is not None:
        return False, False

    is_owner_or_admin = bool(
        current_user and (current_user.role == "admin" or current_user.id == dataset.owner_id)
    )
    if is_owner_or_admin:
        return True, False

    policy = get_dataset_access_policy(db, dataset.id)
    if policy and policy.access_level == ACCESS_LEVEL_PASSWORD_PROTECTED:
        if dataset.dataset_status not in PUBLIC_VISIBLE_STATUSES:
            return False, False
        if not dataset_has_published_version(db, dataset.id):
            return False, False
        if verify_dataset_access_token(str(dataset.id), access_token):
            return True, False
        return False, True

    if is_dataset_publicly_browsable(db, dataset):
        return True, False

    return False, False


def verify_dataset_access_password(db: Session, dataset: Dataset, password: str) -> bool:
    policy = get_dataset_access_policy(db, dataset.id)
    if not policy or policy.access_level != ACCESS_LEVEL_PASSWORD_PROTECTED:
        return False
    if not policy.password_hash:
        return False
    # Backward compatibility with existing bcrypt hashes
    if policy.password_hash.startswith("$2b$"):
        return verify_password(password, policy.password_hash)
    # Direct comparison if stored as plain text
    return password == policy.password_hash


def set_dataset_access_policy(
    *,
    db: Session,
    dataset: Dataset,
    access_level: str,
    access_password: str | None,
) -> DatasetAccessPolicy:
    if access_level not in {ACCESS_LEVEL_PUBLIC, ACCESS_LEVEL_PASSWORD_PROTECTED}:
        raise ValueError("invalid_access_level")

    policy = get_dataset_access_policy(db, dataset.id)
    if not policy:
        policy = DatasetAccessPolicy(dataset_id=dataset.id)
        db.add(policy)
        db.flush()

    policy.access_level = access_level

    if access_level == ACCESS_LEVEL_PUBLIC:
        policy.password_hash = None
    else:
        next_password = (access_password or "").strip()
        if next_password:
            # We skip the minimum length requirement specifically for auto-generating
            policy.password_hash = next_password
        elif not policy.password_hash:
            raise ValueError("missing_access_password")

    db.add(policy)
    return policy


def public_dataset_visible_filter(db: Session):
    protected_exists = db.query(DatasetAccessPolicy.dataset_id).filter(
        and_(
            DatasetAccessPolicy.dataset_id == Dataset.id,
            DatasetAccessPolicy.access_level == ACCESS_LEVEL_PASSWORD_PROTECTED,
        )
    ).correlate(Dataset).exists()
    published_version_exists = db.query(DatasetVersion.id).filter(
        and_(
            DatasetVersion.dataset_id == Dataset.id,
            DatasetVersion.status == "published",
        )
    ).correlate(Dataset).exists()
    approved_review_exists = db.query(DatasetReviewRequest.id).filter(
        and_(
            DatasetReviewRequest.dataset_id == Dataset.id,
            DatasetReviewRequest.status == "approved",
        )
    ).correlate(Dataset).exists()
    return and_(
        Dataset.dataset_status.in_(tuple(PUBLIC_VISIBLE_STATUSES)),
        ~protected_exists,
        published_version_exists,
        approved_review_exists,
    )
