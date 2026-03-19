import re

with open('/home/zy/zhangyi/rxncommons/backend/app/api/v1/endpoints/datasets.py', 'r') as f:
    content = f.read()

old_str = """    items, total = crud_dataset.get_datasets(
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
    return {"items": items, "total": total}"""

new_str = """    items, total = crud_dataset.get_datasets(
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
    return {"items": items, "total": total}"""

content = content.replace(old_str, new_str)

with open('/home/zy/zhangyi/rxncommons/backend/app/api/v1/endpoints/datasets.py', 'w') as f:
    f.write(content)
