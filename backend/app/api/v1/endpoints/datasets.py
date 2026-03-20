from uuid import UUID
import uuid
import re
import hashlib
import io
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, UploadFile, File, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from app.api import deps
from app.core.storage import minio_client
from app.crud import crud_dataset
from app.schemas.dataset import DatasetCreate, DatasetResponse, DatasetUpdate
from app.schemas.dataset import DatasetListResponse
from app.models.user import User
from app.models.dataset import Dataset, DatasetFile, DatasetVersion, FileColumn, DatasetTag
from app.models.system import HomeFeaturedDataset
from app.models.dataset_access import (
    ACCESS_LEVEL_PASSWORD_PROTECTED,
    ACCESS_LEVEL_PUBLIC,
)
from app.core.dataset_access import (
    attach_access_level,
    create_dataset_access_token,
    evaluate_dataset_access,
    get_dataset_access_policy,
    public_dataset_visible_filter,
    set_dataset_access_policy,
    verify_dataset_access_password,
)

router = APIRouter()
VERSION_MARKER_PATTERN = re.compile(r"(?:^|\b)(?:__SYS_VERSION_NUM__|version_num)\s*=\s*(\d+)\b")


def _extract_requested_version_num(raw_reason: str | None) -> int | None:
    if not raw_reason:
        return None
    match = VERSION_MARKER_PATTERN.search(raw_reason)
    if not match:
        return None
    try:
        return int(match.group(1))
    except Exception:
        return None

@router.post("", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
def create_dataset(
    *,
    db: Session = Depends(deps.get_db),
    dataset_in: DatasetCreate,
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    创建一个新的数据集，初始状态为 draft 草稿，并同时初始化生成 V1 版本的占位记录。
    必须要求当前用户邮箱处于验证通过状态 (is_email_verified)
    """
    if not current_user.is_email_verified:
        raise HTTPException(
            status_code=403, 
            detail="auth_email_not_verified"
        )
        
    dataset = crud_dataset.create_dataset(db=db, dataset_in=dataset_in, owner_id=current_user.id)
    attach_access_level(dataset, None)
    return dataset

from pydantic import BaseModel, Field
class ReviewSubmitReq(BaseModel):
    version_num: int
    version_note: str | None = Field(None, max_length=500)


class DatasetAccessPolicyResp(BaseModel):
    access_level: str
    has_password: bool
    needs_review: bool = False
    message: str | None = None
    dataset_status: str | None = None


class DatasetAccessPolicyUpdateReq(BaseModel):
    access_level: str = ACCESS_LEVEL_PUBLIC
    access_password: str | None = None


class DatasetAccessUnlockReq(BaseModel):
    password: str

@router.get("/by-id/{dataset_id}", response_model=DatasetResponse)
def get_dataset_by_id(
    dataset_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User | None = Depends(deps.get_current_user_optional),
    dataset_access_token: str | None = Header(default=None, alias="X-Dataset-Access-Token"),
):
    """通过 UUID 获取数据集详情"""
    dataset = crud_dataset.get_dataset(db, dataset_id)
    allowed, password_required = evaluate_dataset_access(
        db=db,
        dataset=dataset,
        current_user=current_user,
        access_token=dataset_access_token,
    )
    if not allowed:
        if password_required:
            raise HTTPException(
                status_code=403,
                detail={"code": "dataset_access_password_required"},
            )
        raise HTTPException(status_code=404, detail="dataset_not_found")

    from app.models.dataset import DatasetVersion
    is_owner_or_admin = bool(
        current_user and (current_user.role == "admin" or current_user.id == dataset.owner_id)
    )
    if is_owner_or_admin:
        total_rows = db.query(func.coalesce(func.sum(DatasetFile.row_count), 0)).join(
            DatasetVersion,
            DatasetFile.version_id == DatasetVersion.id,
        ).filter(
            DatasetVersion.dataset_id == dataset.id,
            DatasetVersion.version_num == dataset.current_version,
        ).scalar()
    else:
        public_version = db.query(DatasetVersion).filter(
            DatasetVersion.dataset_id == dataset.id,
            DatasetVersion.status == "published",
        ).order_by(DatasetVersion.version_num.desc()).first()
        if public_version:
            total_rows = db.query(func.coalesce(func.sum(DatasetFile.row_count), 0)).filter(
                DatasetFile.version_id == public_version.id
            ).scalar()
        else:
            total_rows = 0
    setattr(dataset, 'total_rows', int(total_rows or 0))

    from app.models.interaction import DatasetReviewRequest
    latest_submitted_at = db.query(func.max(DatasetReviewRequest.submitted_at)).filter(
        DatasetReviewRequest.dataset_id == dataset.id,
    ).scalar()
    latest_reviewed_at = db.query(func.max(DatasetReviewRequest.reviewed_at)).filter(
        DatasetReviewRequest.dataset_id == dataset.id,
    ).scalar()
    latest_approved_at = db.query(func.max(DatasetReviewRequest.reviewed_at)).filter(
        DatasetReviewRequest.dataset_id == dataset.id,
        DatasetReviewRequest.status == 'approved',
    ).scalar()
    setattr(dataset, 'latest_review_submitted_at', latest_submitted_at)
    setattr(dataset, 'latest_reviewed_at', latest_reviewed_at)
    setattr(dataset, 'latest_approved_at', latest_approved_at)
    attach_access_level(dataset, get_dataset_access_policy(db, dataset.id), include_password=is_owner_or_admin)

    return dataset

@router.post("/{dataset_id}/submit-review")
def submit_review(
    dataset_id: uuid.UUID,
    req: ReviewSubmitReq,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    dataset = crud_dataset.get_dataset(db, dataset_id)
    if not dataset or dataset.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # 支持“已发布数据集新增版本后直接提交审核”的流程：
    # 旧版逻辑只允许 draft/revision_required，会导致 published 数据集的新版本提审报冲突。
    if dataset.dataset_status not in ('draft', 'revision_required', 'published'):
        raise HTTPException(status_code=409, detail="dataset_status_conflict")
    
    from app.models.interaction import DatasetReviewRequest
    from app.models.dataset import DatasetVersion
    version = db.query(DatasetVersion).filter(DatasetVersion.dataset_id==dataset.id, DatasetVersion.version_num==req.version_num).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    if version.status != "draft":
        raise HTTPException(status_code=409, detail="version_not_editable")

    if req.version_note is not None:
        version.version_note = req.version_note

    if not (version.version_note or '').strip():
        raise HTTPException(status_code=422, detail="missing_version_note")
    if len((dataset.description or "").strip()) < 10:
        raise HTTPException(status_code=422, detail="description_too_short")

    task_tag_count = db.query(DatasetTag).filter(
        DatasetTag.dataset_id == dataset.id,
        DatasetTag.tag_type == 'task'
    ).count()
    if task_tag_count == 0:
        raise HTTPException(status_code=422, detail="missing_task_tag")

    version_files = db.query(DatasetFile).filter(DatasetFile.version_id == version.id).all()
    if len(version_files) == 0:
        raise HTTPException(status_code=422, detail="missing_files")

    missing_file_desc = [f.filename for f in version_files if not (f.description or '').strip()]
    if missing_file_desc:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "missing_file_description",
                "files": missing_file_desc,
            }
        )

    for f in version_files:
        cols = db.query(FileColumn).filter(FileColumn.file_id == f.id).all()
        if not cols or any(not (c.description or '').strip() for c in cols):
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "missing_column_description",
                    "file": f.filename,
                }
            )

    # 密码保护数据集不进入管理员审核队列，直接发布当前版本。
    policy = get_dataset_access_policy(db, dataset.id)
    if policy and policy.access_level == ACCESS_LEVEL_PASSWORD_PROTECTED:
        pre_review_status = dataset.dataset_status
        dataset.dataset_status = "published"
        dataset.status_reason = None
        version.status = "published"
        if not dataset.current_version or req.version_num >= int(dataset.current_version):
            dataset.current_version = req.version_num
        
        # 记录一条已通过的审核请求，使管理员能在后台“已通过”列表中看到这个数据集
        auto_review_req = DatasetReviewRequest(
            dataset_id=dataset.id,
            pre_review_status=pre_review_status,
            submitted_by=current_user.id,
            status='approved',
            reviewed_at=func.now(),
            result_reason=f"__SYS_VERSION_NUM__={req.version_num}\n私密数据集自动发布免审",
        )
        db.add(auto_review_req)
        db.commit()
        return {
            "status": "success",
            "message": "Password-protected dataset published without review",
            "auto_published": True,
        }

    # Record pre_review_status for rollback on reject
    pre_review_status = dataset.dataset_status
    if dataset.dataset_status != 'published':
        dataset.dataset_status = 'pending_review'
    dataset.status_reason = None
    version.status = 'pending_review'
    
    review_req = DatasetReviewRequest(
        dataset_id=dataset.id,
        pre_review_status=pre_review_status,
        submitted_by=current_user.id,
        result_reason=f"__SYS_VERSION_NUM__={req.version_num}",
        status='pending'
    )
    db.add(review_req)
    db.commit()
    return {"status": "success", "message": "Review submitted successfully"}


@router.post("/{dataset_id}/cancel-review")
def cancel_review(
    dataset_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    dataset = crud_dataset.get_dataset(db, dataset_id)
    if not dataset or dataset.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    from app.models.interaction import DatasetReviewRequest
    from app.models.dataset import DatasetVersion

    pending_req = db.query(DatasetReviewRequest).enable_eagerloads(False).filter(
        DatasetReviewRequest.dataset_id == dataset.id,
        DatasetReviewRequest.status == "pending"
    ).with_for_update().first()
    if not pending_req:
        raise HTTPException(status_code=409, detail="review_request_not_pending")

    requested_version_num = _extract_requested_version_num(pending_req.result_reason)
    is_access_change = '__SYS_ACCESS_CHANGE__' in (pending_req.result_reason or '')

    # 权限变更审核：版本本身已是 published，不需修改版本状态
    if not is_access_change and requested_version_num is not None:
        version = db.query(DatasetVersion).filter(
            DatasetVersion.dataset_id == dataset.id,
            DatasetVersion.version_num == requested_version_num
        ).first()
        if version and version.status == "pending_review":
            version.status = "draft"

    pending_req.status = "canceled_by_user"
    pending_req.reviewed_at = datetime.utcnow()
    pending_req.reviewed_by = current_user.id
    pending_req.result_reason = "用户取消审核"

    if dataset.dataset_status != 'published':
        dataset.dataset_status = pending_req.pre_review_status or "draft"
    dataset.status_reason = None

    db.commit()
    return {
        "status": "success",
        "message": "Review canceled by user",
        "dataset_status": dataset.dataset_status,
    }


def _extract_human_review_reason(raw: str | None) -> str | None:
    if not raw:
        return None
    kept: list[str] = []
    for line in raw.splitlines():
        stripped = line.strip()
        if re.fullmatch(r"(?:__SYS_VERSION_NUM__|version_num)\s*=\s*\d+", stripped):
            continue
        if stripped.startswith("__SYS_ACCESS_CHANGE__="):
            continue
        if stripped:
            kept.append(line)
    cleaned = "\n".join(kept).strip()
    return cleaned or None


@router.get("/{dataset_id}/review-history")
def get_dataset_review_history(
    dataset_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """返回数据集的审核操作历史，仅数据集所有者或管理员可查看。"""
    dataset = crud_dataset.get_dataset(db, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="dataset_not_found")
    if current_user.role != "admin" and current_user.id != dataset.owner_id:
        raise HTTPException(status_code=403, detail="forbidden")

    from app.models.interaction import DatasetReviewRequest
    history = (
        db.query(DatasetReviewRequest)
        .filter(DatasetReviewRequest.dataset_id == dataset.id)
        .order_by(DatasetReviewRequest.submitted_at.desc())
        .all()
    )
    return [
        {
            "id": str(h.id),
            "status": h.status,
            "submitted_at": h.submitted_at,
            "reviewed_at": h.reviewed_at,
            "result_reason": _extract_human_review_reason(h.result_reason),
            "version_num": _extract_requested_version_num(h.result_reason),
        }
        for h in history
    ]


@router.get("/{dataset_id}/access-policy", response_model=DatasetAccessPolicyResp)
def get_access_policy(
    dataset_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    dataset = crud_dataset.get_dataset(db, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if current_user.role != "admin" and dataset.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    policy = get_dataset_access_policy(db, dataset.id)
    if not policy:
        return DatasetAccessPolicyResp(
            access_level=ACCESS_LEVEL_PUBLIC,
            has_password=False,
            needs_review=False,
            message=None,
            dataset_status=dataset.dataset_status,
        )
    return DatasetAccessPolicyResp(
        access_level=policy.access_level or ACCESS_LEVEL_PUBLIC,
        has_password=bool(policy.password_hash),
        needs_review=False,
        message=None,
        dataset_status=dataset.dataset_status,
    )


@router.put("/{dataset_id}/access-policy", response_model=DatasetAccessPolicyResp)
def update_access_policy(
    dataset_id: UUID,
    payload: DatasetAccessPolicyUpdateReq,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    dataset = crud_dataset.get_dataset(db, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if current_user.role != "admin" and dataset.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    new_level = (payload.access_level or ACCESS_LEVEL_PUBLIC).strip()
    old_policy = get_dataset_access_policy(db, dataset.id)
    old_level = old_policy.access_level if old_policy else ACCESS_LEVEL_PUBLIC

    from app.models.dataset import DatasetVersion
    from app.models.interaction import DatasetReviewRequest

    # 如果有版本正在审核中，禁止切换访问权限
    pending_version = db.query(DatasetVersion).filter(
        DatasetVersion.dataset_id == dataset.id,
        DatasetVersion.status == 'pending_review'
    ).first()
    if pending_version:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "has_pending_review",
                "message": "有版本正在审核中，请先等待审核完成或取消审核后再修改访问权限。",
                "version_num": pending_version.version_num,
            }
        )

    # 如果有权限变更正在审核中，也禁止再次修改
    pending_access_review = db.query(DatasetReviewRequest).filter(
        DatasetReviewRequest.dataset_id == dataset.id,
        DatasetReviewRequest.status == 'pending',
        DatasetReviewRequest.result_reason.contains('__SYS_ACCESS_CHANGE__')
    ).first()
    if pending_access_review:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "has_pending_access_review",
                "message": "有访问权限变更正在审核中，请等待审核完成后再修改。",
            }
        )

    # 私密→公开：已发布的版本内容将公开可见，需要管理员审核
    # 在审核通过前不修改 access_level，以保留密码和私密状态
    if old_level == ACCESS_LEVEL_PASSWORD_PROTECTED and new_level == ACCESS_LEVEL_PUBLIC:
        has_published = db.query(DatasetVersion).filter(
            DatasetVersion.dataset_id == dataset.id,
            DatasetVersion.status == 'published'
        ).first()
        if has_published and dataset.dataset_status == 'published':
            dataset.dataset_status = 'pending_review'
            dataset.status_reason = None
            review_req = DatasetReviewRequest(
                dataset_id=dataset.id,
                pre_review_status='published',
                submitted_by=current_user.id,
                result_reason=f"__SYS_VERSION_NUM__={dataset.current_version}\n__SYS_ACCESS_CHANGE__={ACCESS_LEVEL_PASSWORD_PROTECTED}>{ACCESS_LEVEL_PUBLIC}\n访问权限由私密变更为公开，需审核",
                status='pending'
            )
            db.add(review_req)
            db.commit()
            return {
                "access_level": old_level,
                "has_password": bool(old_policy.password_hash) if old_policy else False,
                "needs_review": True,
                "message": "访问权限变更已提交管理员审核。审核通过后，数据集将对所有用户可见。",
                "dataset_status": dataset.dataset_status,
            }

    # 其他情况（公开→私密、无已发布版本等）直接变更
    try:
        policy = set_dataset_access_policy(
            db=db,
            dataset=dataset,
            access_level=new_level,
            access_password=payload.access_password,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    db.commit()
    db.refresh(policy)
    return {
        "access_level": policy.access_level,
        "has_password": bool(policy.password_hash),
        "needs_review": False,
        "message": None,
        "dataset_status": dataset.dataset_status,
    }


@router.post("/{dataset_id}/access/unlock")
def unlock_dataset_by_id(
    dataset_id: UUID,
    payload: DatasetAccessUnlockReq,
    db: Session = Depends(deps.get_db),
):
    dataset = crud_dataset.get_dataset(db, dataset_id)
    if not dataset or dataset.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    policy = get_dataset_access_policy(db, dataset.id)
    if not policy or policy.access_level != ACCESS_LEVEL_PASSWORD_PROTECTED:
        raise HTTPException(status_code=409, detail="dataset_not_password_protected")

    if not verify_dataset_access_password(db, dataset, payload.password):
        raise HTTPException(status_code=403, detail="invalid_dataset_password")

    token = create_dataset_access_token(dataset)
    return {"status": "success", "access_token": token, "dataset_id": str(dataset.id)}

from app.crud import crud_user

@router.get("", response_model=DatasetListResponse)
def list_datasets(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 10,
    search: Optional[str] = None,
    owner: Optional[str] = None,
    source_type: Optional[str] = None,
    status_filter: Optional[str] = None,
    size_bucket: Optional[str] = None,
    min_rows: Optional[int] = None,
    max_rows: Optional[int] = None,
    sort_order: Optional[str] = None,
    current_user: User | None = Depends(deps.get_current_user_optional),
):
    owner_id = None
    include_private = False
    if owner:
        owner_user = crud_user.get_by_username(db, username=owner)
        if owner_user:
            owner_id = owner_user.id
            include_private = bool(
                current_user and (
                    current_user.role == "admin" or current_user.id == owner_user.id
                )
            )
    items, total = crud_dataset.get_datasets(
        db,
        skip=skip,
        limit=limit,
        search=search,
        owner_id=owner_id,
        include_private=include_private,
        source_type=source_type,
        status_filter=status_filter,
        size_bucket=size_bucket,
        min_rows=min_rows,
        max_rows=max_rows,
        sort_order=sort_order,
    )
    from app.core.dataset_access import attach_access_levels
    attach_access_levels(db, items, include_password=include_private)
    return {"items": items, "total": total}


@router.get("/rows-range")
def get_rows_range(
    db: Session = Depends(deps.get_db),
    search: Optional[str] = None,
    owner: Optional[str] = None,
    source_type: Optional[str] = None,
    current_user: User | None = Depends(deps.get_current_user_optional),
):
    owner_id = None
    include_private = False
    if owner:
        owner_user = crud_user.get_by_username(db, username=owner)
        if owner_user:
            owner_id = owner_user.id
            include_private = bool(
                current_user and (
                    current_user.role == "admin" or current_user.id == owner_user.id
                )
            )

    min_rows, max_rows = crud_dataset.get_dataset_rows_range(
        db,
        search=search,
        owner_id=owner_id,
        include_private=include_private,
        source_type=source_type,
    )
    return {
        "min_rows": int(min_rows),
        "max_rows": int(max_rows),
    }


@router.get("/featured", response_model=DatasetListResponse)
def get_featured_datasets(
    db: Session = Depends(deps.get_db),
    limit: int = 3,
):
    limit = max(1, min(limit, 20))

    featured_rows = db.query(HomeFeaturedDataset).order_by(
        HomeFeaturedDataset.sort_order.asc(),
        HomeFeaturedDataset.created_at.asc(),
    ).all()

    items: list[Dataset] = []
    if featured_rows:
        order_ids = [r.dataset_id for r in featured_rows]
        datasets = db.query(Dataset).filter(
            Dataset.id.in_(order_ids),
            Dataset.deleted_at.is_(None),
            public_dataset_visible_filter(db),
        ).all()
        ds_map = {d.id: d for d in datasets}
        for ds_id in order_ids:
            ds = ds_map.get(ds_id)
            if ds:
                items.append(ds)
            if len(items) >= limit:
                break

    if items:
        dataset_ids = [item.id for item in items]
        latest_published_subq = (
            db.query(
                DatasetVersion.dataset_id.label("dataset_id"),
                func.max(DatasetVersion.version_num).label("version_num"),
            )
            .filter(
                DatasetVersion.dataset_id.in_(dataset_ids),
                DatasetVersion.status == "published",
            )
            .group_by(DatasetVersion.dataset_id)
            .subquery()
        )

        rows_agg = (
            db.query(
                DatasetVersion.dataset_id,
                func.coalesce(func.sum(DatasetFile.row_count), 0).label("total_rows"),
            )
            .join(
                latest_published_subq,
                and_(
                    DatasetVersion.dataset_id == latest_published_subq.c.dataset_id,
                    DatasetVersion.version_num == latest_published_subq.c.version_num,
                ),
            )
            .outerjoin(DatasetFile, DatasetFile.version_id == DatasetVersion.id)
            .group_by(DatasetVersion.dataset_id)
            .all()
        )
        rows_map = {row.dataset_id: int(row.total_rows or 0) for row in rows_agg}

        for item in items:
            setattr(item, "total_rows", rows_map.get(item.id, 0))
            setattr(item, "has_published_version", True)

    return {"items": items, "total": len(items)}


@router.post("/{owner}/{slug}/access/unlock")
def unlock_dataset_by_owner_slug(
    owner: str,
    slug: str,
    payload: DatasetAccessUnlockReq,
    db: Session = Depends(deps.get_db),
):
    user = crud_user.get_by_username(db, username=owner)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    dataset = crud_dataset.get_dataset_by_owner_and_slug(db, owner_id=user.id, slug=slug)
    if not dataset or dataset.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    policy = get_dataset_access_policy(db, dataset.id)
    if not policy or policy.access_level != ACCESS_LEVEL_PASSWORD_PROTECTED:
        raise HTTPException(status_code=409, detail="dataset_not_password_protected")

    if not verify_dataset_access_password(db, dataset, payload.password):
        raise HTTPException(status_code=403, detail="invalid_dataset_password")

    token = create_dataset_access_token(dataset)
    return {"status": "success", "access_token": token, "dataset_id": str(dataset.id)}


class TagCreate(BaseModel):
    tag: str
    tag_type: str = "custom"


@router.post("/{dataset_id}/tags")
def add_tag(
    dataset_id: UUID,
    req: TagCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset or dataset.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if dataset.dataset_status == 'pending_review':
        raise HTTPException(status_code=409, detail="dataset_under_review_locked")

    tag_clean = req.tag.lower().strip()
    import re
    if not re.match(r'^[a-z0-9_]+$', tag_clean):
        raise HTTPException(status_code=422, detail="invalid_tag_format")

    existing = db.query(DatasetTag).filter(DatasetTag.dataset_id == dataset_id, DatasetTag.tag == tag_clean).first()
    if not existing:
        new_tag = DatasetTag(dataset_id=dataset_id, tag=tag_clean, tag_type=req.tag_type)
        db.add(new_tag)
        db.commit()
    return {"status": "success", "tag": tag_clean}


@router.delete("/{dataset_id}/tags/{tag}")
def remove_tag(
    dataset_id: UUID,
    tag: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset or dataset.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if dataset.dataset_status == 'pending_review':
        raise HTTPException(status_code=409, detail="dataset_under_review_locked")

    db.query(DatasetTag).filter(DatasetTag.dataset_id == dataset_id, DatasetTag.tag == tag).delete()
    db.commit()
    return {"status": "success"}


@router.get("/{dataset_id}/tags")
def get_tags(
    dataset_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User | None = Depends(deps.get_current_user_optional),
    dataset_access_token: str | None = Header(default=None, alias="X-Dataset-Access-Token"),
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
            raise HTTPException(
                status_code=403,
                detail={"code": "dataset_access_password_required"},
            )
        raise HTTPException(status_code=404, detail="Dataset not found")

    tags = db.query(DatasetTag).filter(DatasetTag.dataset_id == dataset_id).all()
    return [{"tag": t.tag, "tag_type": t.tag_type} for t in tags]


# Slug conflict check: only counts published / password-protected datasets as "occupied".
# Drafts and pending-review datasets are excluded so they don't block titles.
@router.get("/{owner}/{slug}/slug-check")
def check_slug_conflict(
    owner: str,
    slug: str,
    exclude_id: str | None = None,
    db: Session = Depends(deps.get_db),
):
    ACTIVE_STATUSES = {"published", "archived"}
    owner_user = crud_user.get_by_username(db, username=owner)
    if not owner_user:
        return {"conflict": False}
    q = db.query(Dataset).filter(
        Dataset.owner_id == owner_user.id,
        Dataset.slug == slug,
        Dataset.deleted_at.is_(None),
        Dataset.dataset_status.in_(ACTIVE_STATUSES),
    )
    if exclude_id:
        try:
            from uuid import UUID as _UUID
            q = q.filter(Dataset.id != _UUID(exclude_id))
        except ValueError:
            pass
    conflict = q.first() is not None
    return {"conflict": conflict}


@router.get("/{owner}/{slug}", response_model=DatasetResponse)
def get_dataset(
    owner: str,
    slug: str,
    db: Session = Depends(deps.get_db),
    current_user: User | None = Depends(deps.get_current_user_optional),
    dataset_access_token: str | None = Header(default=None, alias="X-Dataset-Access-Token"),
):
    user = crud_user.get_by_username(db, username=owner)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    dataset = crud_dataset.get_dataset_by_owner_and_slug(db, owner_id=user.id, slug=slug)
    allowed, password_required = evaluate_dataset_access(
        db=db,
        dataset=dataset,
        current_user=current_user,
        access_token=dataset_access_token,
    )
    if not allowed:
        if password_required:
            raise HTTPException(
                status_code=403,
                detail={"code": "dataset_access_password_required"},
            )
        raise HTTPException(status_code=404, detail="Dataset not found")

    is_owner_or_admin = bool(current_user and (current_user.role == "admin" or current_user.id == dataset.owner_id))
    attach_access_level(dataset, get_dataset_access_policy(db, dataset.id), include_password=is_owner_or_admin)
    return dataset

@router.put("/{dataset_id}/archive")
def archive_dataset(
    dataset_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset or dataset.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    if dataset.dataset_status not in ["published", "revision_required"]:
        raise HTTPException(status_code=409, detail="dataset_status_conflict")
        
    dataset.pre_archive_status = dataset.dataset_status
    dataset.dataset_status = "archived"
    db.commit()
    return {"status": "success", "message": "Dataset archived"}

@router.put("/{dataset_id}/unarchive")
def unarchive_dataset(
    dataset_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset or dataset.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    if dataset.dataset_status != "archived":
        raise HTTPException(status_code=409, detail="Dataset is not archived")
        
    dataset.dataset_status = dataset.pre_archive_status or "published"
    dataset.pre_archive_status = None
    db.commit()
    return {"status": "success", "message": "Dataset unarchived"}

@router.delete("/{owner}/{slug}")
def delete_dataset(
    owner: str,
    slug: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    from app.crud import crud_user
    owner_user = crud_user.get_by_username(db, username=owner)
    if not owner_user:
        raise HTTPException(status_code=404, detail="Owner not found")
        
    dataset = db.query(Dataset).filter(Dataset.owner_id == owner_user.id, Dataset.slug == slug, Dataset.deleted_at.is_(None)).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    if dataset.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    if dataset.dataset_status == "takedown":
        raise HTTPException(status_code=409, detail="Cannot delete takedown dataset")

    crud_dataset.soft_delete_dataset(
        db,
        dataset=dataset,
        deleted_by=current_user.id,
    )

    db.commit()
    return {"status": "success", "message": "Dataset deleted"}

@router.put("/{owner}/{slug}", response_model=DatasetResponse)
def update_dataset(
    owner: str,
    slug: str,
    req: DatasetUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    owner_user = crud_user.get_by_username(db, username=owner)
    if not owner_user:
        raise HTTPException(status_code=404, detail="Owner not found")
        
    dataset = crud_dataset.get_dataset_by_owner_and_slug(db, owner_id=owner_user.id, slug=slug)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    if dataset.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    if dataset.dataset_status == 'pending_review':
        raise HTTPException(status_code=409, detail="dataset_under_review_locked")
        
    if req.title is not None:
        next_title = req.title.strip()
        if not next_title:
            raise HTTPException(status_code=422, detail="invalid_title")
        if next_title != dataset.title:
            dataset.slug = crud_dataset.generate_unique_slug(
                db,
                owner_id=dataset.owner_id,
                title=next_title,
                exclude_dataset_id=dataset.id,
            )
        dataset.title = next_title
    if req.description is not None:
        dataset.description = req.description
    if req.source_type is not None:
        dataset.source_type = req.source_type
    if req.source_ref is not None:
        dataset.source_ref = req.source_ref
    if req.license is not None:
        dataset.license = req.license
        
    db.commit()
    db.refresh(dataset)
    is_owner_or_admin = bool(current_user and (current_user.role == "admin" or current_user.id == dataset.owner_id))
    attach_access_level(dataset, get_dataset_access_policy(db, dataset.id), include_password=is_owner_or_admin)
    return dataset


@router.put("/by-id/{dataset_id}/meta", response_model=DatasetResponse)
def update_dataset_by_id(
    dataset_id: UUID,
    req: DatasetUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    dataset = crud_dataset.get_dataset(db, dataset_id)
    if not dataset or dataset.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    if dataset.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    if dataset.dataset_status == 'pending_review':
        raise HTTPException(status_code=409, detail="dataset_under_review_locked")

    if req.title is not None:
        next_title = req.title.strip()
        if not next_title:
            raise HTTPException(status_code=422, detail="invalid_title")
        if next_title != dataset.title:
            dataset.slug = crud_dataset.generate_unique_slug(
                db,
                owner_id=dataset.owner_id,
                title=next_title,
                exclude_dataset_id=dataset.id,
            )
        dataset.title = next_title
    if req.description is not None:
        dataset.description = req.description
    if req.source_type is not None:
        dataset.source_type = req.source_type
    if req.source_ref is not None:
        dataset.source_ref = req.source_ref
    if req.license is not None:
        dataset.license = req.license

    db.commit()
    db.refresh(dataset)
    is_owner_or_admin = bool(current_user and (current_user.role == "admin" or current_user.id == dataset.owner_id))
    attach_access_level(dataset, get_dataset_access_policy(db, dataset.id), include_password=is_owner_or_admin)
    return dataset


ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB

IMAGE_CONTENT_TYPES = {
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.webp': 'image/webp',
}


@router.post("/by-id/{dataset_id}/cover-image")
def upload_cover_image(
    dataset_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    dataset = crud_dataset.get_dataset(db, dataset_id)
    if not dataset or dataset.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if dataset.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    import os
    ext = os.path.splitext(file.filename or '')[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(status_code=422, detail="仅支持 jpg/jpeg/png/gif/webp 格式的图片")

    data = file.file.read()
    if not data:
        raise HTTPException(status_code=422, detail="图片内容为空")
    if len(data) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=422, detail="图片大小不能超过 5 MB")

    file_hash = hashlib.sha256(data).hexdigest()[:16]
    object_key = f"covers/{dataset_id}_{file_hash}{ext}"
    content_type = IMAGE_CONTENT_TYPES.get(ext, 'application/octet-stream')

    minio_client.put_object(
        "rxncommons-bucket",
        object_key,
        io.BytesIO(data),
        length=len(data),
        content_type=content_type,
    )

    # 如果旧的 cover_image_key 存在且不同，尝试删除旧对象
    old_key = dataset.cover_image_key
    if old_key and old_key != object_key:
        try:
            minio_client.remove_object("rxncommons-bucket", old_key)
        except Exception:
            pass

    dataset.cover_image_key = object_key
    db.commit()
    return {"status": "success", "cover_image_key": object_key}


@router.get("/by-id/{dataset_id}/cover-image")
def get_cover_image(
    dataset_id: UUID,
    db: Session = Depends(deps.get_db),
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.deleted_at.is_(None)).first()
    if not dataset or not dataset.cover_image_key:
        raise HTTPException(status_code=404, detail="No cover image")

    import os
    ext = os.path.splitext(dataset.cover_image_key)[1].lower()
    content_type = IMAGE_CONTENT_TYPES.get(ext, 'application/octet-stream')

    try:
        response = minio_client.get_object("rxncommons-bucket", dataset.cover_image_key)
        def stream_cover_image():
            try:
                yield from response.stream(32 * 1024)
            finally:
                response.close()
                response.release_conn()

        return StreamingResponse(
            stream_cover_image(),
            media_type=content_type,
            headers={"Cache-Control": "public, max-age=86400"},
        )
    except Exception:
        raise HTTPException(status_code=404, detail="Cover image not found in storage")


@router.delete("/by-id/{dataset_id}/cover-image")
def delete_cover_image(
    dataset_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    dataset = crud_dataset.get_dataset(db, dataset_id)
    if not dataset or dataset.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if dataset.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    if not dataset.cover_image_key:
        return {"status": "success"}

    try:
        minio_client.remove_object("rxncommons-bucket", dataset.cover_image_key)
    except Exception:
        pass
    dataset.cover_image_key = None
    db.commit()
    return {"status": "success"}
