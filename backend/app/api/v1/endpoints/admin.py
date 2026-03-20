from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel
from app.core.tasks import pack_version_archive
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy import or_, and_
from typing import List, Optional
from uuid import UUID
from app.api import deps
from app.crud import crud_dataset
from app.core.dataset_access import attach_access_levels, public_dataset_visible_filter
from app.models.user import User
from app.models.dataset import Dataset, DatasetVersion, DatasetFile, FileColumn
from app.models.dataset_access import ACCESS_LEVEL_PASSWORD_PROTECTED, DatasetAccessPolicy
from app.models.interaction import DatasetReviewRequest, AdminSuggestion
from app.models.system import HomeFeaturedDataset
from app.schemas.admin import ReviewRequestResponse, ReviewRequestListResponse, ReviewRejectReq, SuggestionCreate, UserQuotaUpdate, UserAdminUpdateBase
from app.schemas.user import UserResponse
from datetime import datetime
import re

router = APIRouter()

def get_current_admin(current_user: User = Depends(deps.get_current_active_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user


PUBLIC_STATUSES = ["published"]
VERSION_MARKER_PATTERN = re.compile(r"(?:^|\b)(?:__SYS_VERSION_NUM__|version_num)\s*=\s*(\d+)\b")
ACCESS_CHANGE_PATTERN = re.compile(r"__SYS_ACCESS_CHANGE__=(\w+)>(\w+)")


def _extract_requested_version_num(req: DatasetReviewRequest) -> Optional[int]:
    raw = req.result_reason or ""
    match = VERSION_MARKER_PATTERN.search(raw)
    if not match:
        return None
    try:
        return int(match.group(1))
    except Exception:
        return None


def _extract_access_change(req: DatasetReviewRequest) -> tuple[str, str] | None:
    """Extract access-level change info (old_level, new_level) from review request."""
    raw = req.result_reason or ""
    match = ACCESS_CHANGE_PATTERN.search(raw)
    if not match:
        return None
    return (match.group(1), match.group(2))


def _extract_human_review_reason(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    kept_lines: list[str] = []
    for line in raw.splitlines():
        stripped = line.strip()
        if re.fullmatch(r"(?:__SYS_VERSION_NUM__|version_num)\s*=\s*\d+", stripped):
            continue
        if stripped.startswith("__SYS_ACCESS_CHANGE__="):
            continue
        if stripped:
            kept_lines.append(line)
    cleaned = "\n".join(kept_lines).strip()
    return cleaned or None


def _compose_review_reason(version_num: Optional[int], human_reason: Optional[str], access_change: tuple[str, str] | None = None) -> Optional[str]:
    parts: list[str] = []
    if version_num is not None:
        parts.append(f"__SYS_VERSION_NUM__={version_num}")
    if access_change:
        parts.append(f"__SYS_ACCESS_CHANGE__={access_change[0]}>{access_change[1]}")
    reason = (human_reason or "").strip()
    if reason:
        parts.append(reason)
    if not parts:
        return None
    return "\n".join(parts)


class FeaturedReorderReq(BaseModel):
    dataset_ids: List[UUID]


@router.get("/home-featured")
def list_home_featured(
    db: Session = Depends(deps.get_db),
    admin: User = Depends(get_current_admin)
):
    rows = db.query(HomeFeaturedDataset).order_by(HomeFeaturedDataset.sort_order.asc(), HomeFeaturedDataset.created_at.asc()).all()
    if not rows:
        return []

    dataset_ids = [r.dataset_id for r in rows]
    datasets = db.query(Dataset).filter(
        Dataset.id.in_(dataset_ids),
        Dataset.deleted_at.is_(None)
    ).all()
    ds_map = {d.id: d for d in datasets}

    result = []
    for r in rows:
        ds = ds_map.get(r.dataset_id)
        if not ds:
            continue
        result.append({
            "dataset_id": str(ds.id),
            "title": ds.title,
            "dataset_status": ds.dataset_status,
            "sort_order": r.sort_order,
        })
    return result


@router.post("/home-featured/{dataset_id}")
def add_home_featured(
    dataset_id: UUID,
    db: Session = Depends(deps.get_db),
    admin: User = Depends(get_current_admin)
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.deleted_at.is_(None)).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if dataset.dataset_status not in PUBLIC_STATUSES:
        raise HTTPException(status_code=409, detail="dataset_status_not_public")
    access_policy = db.query(DatasetAccessPolicy).filter(DatasetAccessPolicy.dataset_id == dataset_id).first()
    if access_policy and access_policy.access_level == ACCESS_LEVEL_PASSWORD_PROTECTED:
        raise HTTPException(status_code=409, detail="privacy_dataset_cannot_be_featured")

    existing = db.query(HomeFeaturedDataset).filter(HomeFeaturedDataset.dataset_id == dataset_id).first()
    if existing:
        return {"status": "success", "message": "already_featured"}

    max_sort = db.query(func.coalesce(func.max(HomeFeaturedDataset.sort_order), -1)).scalar() or -1
    db.add(HomeFeaturedDataset(
        dataset_id=dataset_id,
        sort_order=int(max_sort) + 1,
        created_by=admin.id,
    ))
    db.commit()
    return {"status": "success"}


@router.delete("/home-featured/{dataset_id}")
def remove_home_featured(
    dataset_id: UUID,
    db: Session = Depends(deps.get_db),
    admin: User = Depends(get_current_admin)
):
    row = db.query(HomeFeaturedDataset).filter(HomeFeaturedDataset.dataset_id == dataset_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="featured_dataset_not_found")
    db.delete(row)
    db.commit()
    return {"status": "success"}


@router.put("/home-featured/reorder")
def reorder_home_featured(
    req: FeaturedReorderReq,
    db: Session = Depends(deps.get_db),
    admin: User = Depends(get_current_admin)
):
    rows = db.query(HomeFeaturedDataset).all()
    row_map = {r.dataset_id: r for r in rows}

    for idx, dataset_id in enumerate(req.dataset_ids):
        row = row_map.get(dataset_id)
        if row:
            row.sort_order = idx

    db.commit()
    return {"status": "success"}


@router.delete("/datasets/{dataset_id}")
def admin_delete_dataset(
    dataset_id: UUID,
    db: Session = Depends(deps.get_db),
    admin: User = Depends(get_current_admin)
):
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.deleted_at.is_(None),
    ).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if dataset.dataset_status == "takedown":
        raise HTTPException(status_code=409, detail="Cannot delete takedown dataset")

    crud_dataset.soft_delete_dataset(
        db,
        dataset=dataset,
        deleted_by=admin.id,
    )
    db.commit()
    return {"status": "success", "message": "Dataset deleted"}


@router.get("/datasets/deleted")
def list_deleted_datasets(
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(deps.get_db),
    admin: User = Depends(get_current_admin)
):
    query = db.query(Dataset).join(
        User,
        User.id == Dataset.owner_id,
    ).filter(
        Dataset.deleted_at.is_not(None),
    )

    if search:
        like = f"%{search.lower()}%"
        query = query.filter(
            or_(
                func.lower(Dataset.title).like(like),
                func.lower(User.username).like(like),
            )
        )

    total = query.count()
    rows = query.order_by(Dataset.deleted_at.desc(), Dataset.updated_at.desc()).offset(max(skip, 0)).limit(min(max(limit, 1), 100)).all()

    return {
        "items": [
            {
                "id": str(ds.id),
                "title": ds.title,
                "slug": ds.slug,
                "deleted_at": ds.deleted_at,
                "owner": {
                    "username": ds.owner.username if ds.owner else None,
                },
            }
            for ds in rows
        ],
        "total": total,
    }


# Keep a dedicated clear endpoint to avoid path collision with `/datasets/{dataset_id}`.
@router.delete("/datasets/deleted/clear")
def clear_deleted_datasets(
    db: Session = Depends(deps.get_db),
    admin: User = Depends(get_current_admin)
):
    deleted_datasets = db.query(Dataset).filter(
        Dataset.deleted_at.is_not(None),
    ).all()

    purged_count = 0
    for dataset in deleted_datasets:
        crud_dataset.hard_delete_dataset(db, dataset=dataset)
        purged_count += 1

    db.commit()
    return {"status": "success", "purged_count": purged_count}

@router.get("/review-requests", response_model=ReviewRequestListResponse)
def list_review_requests(
    status_filter: Optional[str] = None,
    visibility_filter: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    sort_by: str = "submitted_at",
    sort_order: str = "desc",
    db: Session = Depends(deps.get_db),
    admin: User = Depends(get_current_admin)
):
    owner_alias = User

    # 审核工作台应按“审核请求记录”展示，而不是每个数据集只保留最新一条。
    # 否则当已发布数据集再次提交新版本审核时，旧版本那条 approved 记录会被最新 pending 记录覆盖，
    # 导致“已通过”筛选和计数都失真。
    base_query = db.query(DatasetReviewRequest).join(
        Dataset,
        Dataset.id == DatasetReviewRequest.dataset_id,
    ).join(
        owner_alias,
        owner_alias.id == Dataset.owner_id,
    ).filter(
        Dataset.deleted_at.is_(None),
    )

    if search:
        like = f"%{search.lower()}%"
        base_query = base_query.filter(
            or_(
                func.lower(Dataset.title).like(like),
                func.lower(owner_alias.username).like(like),
            )
        )

    if visibility_filter == "public_visible":
        base_query = base_query.filter(public_dataset_visible_filter(db))
    elif visibility_filter == "password_protected":
        protected_exists = db.query(DatasetAccessPolicy.dataset_id).filter(
            DatasetAccessPolicy.dataset_id == Dataset.id,
            DatasetAccessPolicy.access_level == ACCESS_LEVEL_PASSWORD_PROTECTED,
        ).exists()
        base_query = base_query.filter(protected_exists)

    status_counts_rows = base_query.with_entities(
        DatasetReviewRequest.status,
        func.count(DatasetReviewRequest.id)
    ).group_by(DatasetReviewRequest.status).all()
    status_counts = {status: count for status, count in status_counts_rows}

    query = base_query
    if status_filter and status_filter != 'all':
        statuses = [s.strip() for s in status_filter.split(',') if s.strip()]
        if statuses:
            query = query.filter(DatasetReviewRequest.status.in_(statuses))

    total = query.count()

    sort_map = {
        "submitted_at": DatasetReviewRequest.submitted_at,
        "reviewed_at": DatasetReviewRequest.reviewed_at,
    }
    sort_col = sort_map.get(sort_by, DatasetReviewRequest.submitted_at)
    order_clause = sort_col.asc() if sort_order == 'asc' else sort_col.desc()

    items = query.order_by(order_clause).offset(max(skip, 0)).limit(min(max(limit, 1), 100)).all()
    for item in items:
        setattr(item, "version_num", _extract_requested_version_num(item))
    attach_access_levels(db, [r.dataset for r in items if r.dataset is not None])
    return {
        "items": items,
        "total": total,
        "status_counts": status_counts,
    }


@router.get("/review-requests/{request_id}")
def get_review_request_detail(
    request_id: UUID,
    db: Session = Depends(deps.get_db),
    admin: User = Depends(get_current_admin)
):
    req = db.query(DatasetReviewRequest).filter(DatasetReviewRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Review request not found")

    dataset = db.query(Dataset).filter(Dataset.id == req.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    versions = db.query(DatasetVersion).filter(DatasetVersion.dataset_id == dataset.id).order_by(DatasetVersion.version_num.desc()).all()
    requested_version_num = _extract_requested_version_num(req)
    target_version_num = requested_version_num or dataset.current_version or (versions[0].version_num if versions else None)

    if requested_version_num is None and req.status in {"pending", "rejected", "revision_required", "canceled_by_user"}:
        draft_like = next((v for v in versions if v.status in {"draft", "pending_review", "revision_required"}), None)
        if draft_like:
            target_version_num = draft_like.version_num

    target_version = None
    if target_version_num is not None:
        target_version = db.query(DatasetVersion).filter(
            DatasetVersion.dataset_id == dataset.id,
            DatasetVersion.version_num == target_version_num
        ).first()
    if not target_version and versions:
        target_version = versions[0]
        target_version_num = target_version.version_num

    files = []
    if target_version:
        version_files = db.query(DatasetFile).filter(DatasetFile.version_id == target_version.id).all()
        for f in version_files:
            columns = db.query(FileColumn).filter(FileColumn.file_id == f.id).all()
            files.append({
                "id": str(f.id),
                "filename": f.filename,
                "file_size": f.file_size,
                "description": f.description,
                "row_count": f.row_count,
                "columns": [
                    {
                        "column_name": c.column_name,
                        "column_type": c.column_type,
                        "description": c.description,
                    }
                    for c in columns
                ]
            })

    history_reqs = db.query(DatasetReviewRequest).filter(DatasetReviewRequest.dataset_id == dataset.id).order_by(DatasetReviewRequest.submitted_at.desc()).all()
    history = []
    for hr in history_reqs:
        history.append({
            "id": str(hr.id),
            "status": hr.status,
            "submitted_at": hr.submitted_at,
            "reviewed_at": hr.reviewed_at,
            "result_reason": _extract_human_review_reason(hr.result_reason),
            "version_num": _extract_requested_version_num(hr)
        })

    return {
        "history": history,
        "request": {
            "id": str(req.id),
            "status": req.status,
            "submitted_at": req.submitted_at,
            "submitted_by": str(req.submitted_by),
            "reviewed_at": req.reviewed_at,
            "reviewed_by": str(req.reviewed_by) if req.reviewed_by else None,
            "requested_version_num": requested_version_num,
            "result_reason": _extract_human_review_reason(req.result_reason),
        },
        "dataset": {
            "id": str(dataset.id),
            "title": dataset.title,
            "slug": dataset.slug,
            "dataset_status": dataset.dataset_status,
            "owner_id": str(dataset.owner_id),
            "description": dataset.description,
            "source_type": dataset.source_type,
            "source_ref": dataset.source_ref,
            "license": dataset.license,
            "status_reason": dataset.status_reason,
            "cover_image_key": dataset.cover_image_key,
        },
        "version": {
            "version_num": target_version_num,
            "version_note": target_version.version_note if target_version else None,
            "status": target_version.status if target_version else None,
        },
        "files": files,
    }

class ReviewApproveReq(BaseModel):
    result_reason: Optional[str] = None

@router.post("/review-requests/{request_id}/approve")
def approve_review_request(
    request_id: UUID,
    background_tasks: BackgroundTasks,
    payload: ReviewApproveReq | None = None,
    db: Session = Depends(deps.get_db),
    admin: User = Depends(get_current_admin)
):
    req = db.query(DatasetReviewRequest).enable_eagerloads(False).filter(DatasetReviewRequest.id == request_id).with_for_update().first()
    if not req:
        raise HTTPException(status_code=404, detail="Review request not found")
    if req.status != "pending":
        raise HTTPException(status_code=409, detail="review_request_already_decided")
        
    dataset = db.query(Dataset).filter(Dataset.id == req.dataset_id).first()
    requested_version_num = _extract_requested_version_num(req)
    access_change = _extract_access_change(req)

    if requested_version_num is not None:
        version = db.query(DatasetVersion).filter(
            DatasetVersion.dataset_id == req.dataset_id,
            DatasetVersion.version_num == requested_version_num
        ).first()
    else:
        version = db.query(DatasetVersion).filter(DatasetVersion.dataset_id == req.dataset_id).order_by(DatasetVersion.version_num.desc()).first()
    
    if not dataset or not version:
        raise HTTPException(status_code=404, detail="Dataset or version not found")
        
    reason = ((payload.result_reason if payload else "") or "").strip()

    req.status = "approved"
    req.result_reason = _compose_review_reason(requested_version_num, reason, access_change=access_change)
    req.reviewed_at = datetime.utcnow()
    req.reviewed_by = admin.id
    
    dataset.dataset_status = "published"
    dataset.status_reason = reason or None
    # Update current version if newly approved version is higher or currently None
    if not dataset.current_version or version.version_num > dataset.current_version:
        dataset.current_version = version.version_num
        
    version.status = "published"
    version.metadata_complete = True
    # Normally emit task to sync search_document and generate zip
    background_tasks.add_task(pack_version_archive, version.id)

    # 权限变更审核通过：此时才真正执行 access_level 变更
    if access_change:
        from app.core.dataset_access import set_dataset_access_policy
        set_dataset_access_policy(
            db=db,
            dataset=dataset,
            access_level=access_change[1],
            access_password=None,
        )

    
    db.commit()
    return {"status": "success", "message": "Dataset published"}

@router.post("/review-requests/{request_id}/reject")
def reject_review_request(
    request_id: UUID,
    payload: ReviewRejectReq,
    db: Session = Depends(deps.get_db),
    admin: User = Depends(get_current_admin)
):
    req = db.query(DatasetReviewRequest).enable_eagerloads(False).filter(DatasetReviewRequest.id == request_id).with_for_update().first()
    if not req:
        raise HTTPException(status_code=404, detail="Review request not found")
    if req.status != "pending":
        raise HTTPException(status_code=409, detail="review_request_already_decided")
        
    dataset = db.query(Dataset).filter(Dataset.id == req.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    reason = payload.result_reason.strip()

    requested_version_num = _extract_requested_version_num(req)
    access_change = _extract_access_change(req)

    req.status = "rejected"
    req.result_reason = _compose_review_reason(requested_version_num, reason, access_change=access_change)
    req.reviewed_at = datetime.utcnow()
    req.reviewed_by = admin.id

    # 权限变更审核：版本本身已是 published，不应改动
    if not access_change and requested_version_num is not None:
        version = db.query(DatasetVersion).filter(
            DatasetVersion.dataset_id == req.dataset_id,
            DatasetVersion.version_num == requested_version_num
        ).first()
        if version:
            version.status = "draft"
    
    # Revert dataset status to pre_review_status
    if dataset.dataset_status != 'published':
        dataset.dataset_status = req.pre_review_status or "draft"
    dataset.status_reason = reason
    
    db.commit()
    return {"status": "success", "message": "Dataset rejected"}

class ReviewSuggestReq(BaseModel):
    result_reason: str


class RollbackApprovalReq(BaseModel):
    result_reason: str

@router.post("/review-requests/{request_id}/suggest")
def suggest_revision_via_review(
    request_id: UUID,
    payload: ReviewSuggestReq,
    db: Session = Depends(deps.get_db),
    admin: User = Depends(get_current_admin)
):
    req = db.query(DatasetReviewRequest).enable_eagerloads(False).filter(DatasetReviewRequest.id == request_id).with_for_update().first()
    if not req:
        raise HTTPException(status_code=404, detail="Review request not found")
    if req.status != "pending":
        raise HTTPException(status_code=409, detail="review_request_already_decided")

    dataset = db.query(Dataset).filter(Dataset.id == req.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    reason = payload.result_reason.strip()

    requested_version_num = _extract_requested_version_num(req)
    access_change = _extract_access_change(req)

    req.status = "revision_required"
    req.result_reason = _compose_review_reason(requested_version_num, reason, access_change=access_change)
    req.reviewed_at = datetime.utcnow()
    req.reviewed_by = admin.id

    # 权限变更审核：版本本身已是 published，不应改动
    if not access_change and requested_version_num is not None:
        version = db.query(DatasetVersion).filter(
            DatasetVersion.dataset_id == req.dataset_id,
            DatasetVersion.version_num == requested_version_num
        ).first()
        if version:
            version.status = "draft"

    if dataset.dataset_status != 'published':
            dataset.dataset_status = "revision_required"
    dataset.status_reason = reason

    db.commit()
    return {"status": "success", "message": "Revision suggested"}


@router.post("/review-requests/{request_id}/rollback-approval")
def rollback_approved_review(
    request_id: UUID,
    payload: RollbackApprovalReq,
    db: Session = Depends(deps.get_db),
    admin: User = Depends(get_current_admin)
):
    req = db.query(DatasetReviewRequest).enable_eagerloads(False).filter(DatasetReviewRequest.id == request_id).with_for_update().first()
    if not req:
        raise HTTPException(status_code=404, detail="Review request not found")
    if req.status != "approved":
        raise HTTPException(status_code=409, detail="review_request_not_approved")

    dataset = db.query(Dataset).filter(Dataset.id == req.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    reason = payload.result_reason.strip()

    requested_version_num = _extract_requested_version_num(req)
    access_change = _extract_access_change(req)

    req.status = "revision_required"
    req.result_reason = _compose_review_reason(requested_version_num, reason, access_change=access_change)
    req.reviewed_at = datetime.utcnow()
    req.reviewed_by = admin.id

    if access_change:
        # 权限变更审核被回滚：撤回已执行的 access_level 变更
        # 直接操作 policy，因为原密码已在审核通过时清除无法恢复
        from app.core.dataset_access import get_dataset_access_policy
        from app.models.dataset_access import ACCESS_LEVEL_PASSWORD_PROTECTED as PP
        policy = get_dataset_access_policy(db, dataset.id)
        if policy:
            policy.access_level = PP
            # password_hash 保持为 None，所有者需重新设置密码
    elif requested_version_num is not None:
        version = db.query(DatasetVersion).filter(
            DatasetVersion.dataset_id == req.dataset_id,
            DatasetVersion.version_num == requested_version_num
        ).first()
        if version:
            version.status = "draft"

    # 将数据集拉回需修订，保留可见性并允许作者修正后重提
    if dataset.dataset_status != 'published':
            dataset.dataset_status = "revision_required"
    dataset.status_reason = reason

    db.commit()
    return {"status": "success", "message": "Approval rolled back to revision_required"}

@router.post("/datasets/{dataset_id}/suggest")
def suggest_changes(
    dataset_id: UUID,
    payload: SuggestionCreate,
    db: Session = Depends(deps.get_db),
    admin: User = Depends(get_current_admin)
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    if dataset.dataset_status not in ["published", "revision_required"]:
        raise HTTPException(status_code=409, detail="dataset_status_conflict")
        
    suggestion_text = payload.suggestion_text.strip()

    # Mark as revision_required
    if dataset.dataset_status != 'published':
            dataset.dataset_status = "revision_required"
    dataset.status_reason = suggestion_text
    
    suggestion = AdminSuggestion(
        dataset_id=dataset.id,
        created_by=admin.id,
        recipient_user_id=dataset.owner_id,
        suggestion_text=suggestion_text,
        status="pending"
    )
    db.add(suggestion)
    db.commit()
    # would also create a notification here
    return {"status": "success", "message": "Suggestion created"}

@router.put("/datasets/{dataset_id}/takedown")
def takedown_dataset(
    dataset_id: UUID,
    db: Session = Depends(deps.get_db),
    admin: User = Depends(get_current_admin)
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    dataset.dataset_status = "takedown"
    dataset.status_reason = None
    db.commit()
    return {"status": "success", "message": "Dataset taken down"}

@router.put("/datasets/{dataset_id}/restore")
def restore_dataset(
    dataset_id: UUID,
    db: Session = Depends(deps.get_db),
    admin: User = Depends(get_current_admin)
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    if dataset.deleted_at is not None or dataset.dataset_status == "deleted":
        crud_dataset.restore_soft_deleted_dataset(db, dataset=dataset)
        dataset.status_reason = None
    elif dataset.dataset_status == "takedown":
        latest_published = db.query(DatasetVersion).filter(
            DatasetVersion.dataset_id == dataset.id,
            DatasetVersion.status == "published",
        ).order_by(DatasetVersion.version_num.desc()).first()
        if latest_published:
            dataset.dataset_status = "published"
            dataset.current_version = latest_published.version_num
        else:
            if dataset.dataset_status != 'published':
                dataset.dataset_status = "revision_required"
        dataset.status_reason = None
    else:
        raise HTTPException(status_code=409, detail="Dataset is not in a restorable status")

    db.commit()
    return {"status": "success", "message": "Dataset restored"}

@router.get("/users", response_model=List[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    admin: User = Depends(get_current_admin)
):
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.put("/users/{user_id}/status")
def update_user_status(
    user_id: UUID,
    payload: UserAdminUpdateBase,
    db: Session = Depends(deps.get_db),
    admin: User = Depends(get_current_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if payload.is_active is not None:
        user.is_active = payload.is_active
    db.commit()
    return {"status": "success"}

@router.put("/users/{user_id}/quota")
def update_user_quota(
    user_id: UUID,
    payload: UserQuotaUpdate,
    db: Session = Depends(deps.get_db),
    admin: User = Depends(get_current_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.storage_quota = payload.quota_bytes
    db.commit()
    return {"status": "success", "new_quota": user.storage_quota}
