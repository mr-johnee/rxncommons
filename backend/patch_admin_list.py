import re

with open("/home/zy/zhangyi/rxncommons/backend/app/api/v1/endpoints/admin.py", "r", encoding="utf-8") as f:
    text = f.read()

old_query_base = """def list_review_requests(
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
    base_query = db.query(DatasetReviewRequest).join(
        Dataset,
        Dataset.id == DatasetReviewRequest.dataset_id,
    ).join(
        owner_alias,
        owner_alias.id == Dataset.owner_id,
    )"""

new_query_base = """def list_review_requests(
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
    
    # Subquery for latest review request per dataset
    subquery = db.query(
        DatasetReviewRequest.dataset_id,
        func.max(DatasetReviewRequest.submitted_at).label('max_time')
    ).group_by(DatasetReviewRequest.dataset_id).subquery()

    # Main query joining with subquery to get only latest request rows
    base_query = db.query(DatasetReviewRequest).join(
        subquery,
        and_(
            DatasetReviewRequest.dataset_id == subquery.c.dataset_id,
            DatasetReviewRequest.submitted_at == subquery.c.max_time
        )
    ).join(
        Dataset,
        Dataset.id == DatasetReviewRequest.dataset_id,
    ).join(
        owner_alias,
        owner_alias.id == Dataset.owner_id,
    )"""

if old_query_base in text:
    text = text.replace(old_query_base, new_query_base)
    with open("/home/zy/zhangyi/rxncommons/backend/app/api/v1/endpoints/admin.py", "w", encoding="utf-8") as f:
        f.write(text)
    print("Patched list_review_requests")
else:
    print("Could not find old_query_base")
