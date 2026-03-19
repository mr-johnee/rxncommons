with open('/home/zy/zhangyi/rxncommons/backend/app/core/dataset_access.py', 'r') as f:
    content = f.read()

import re

old_str = """def attach_access_level(dataset: Dataset, policy: DatasetAccessPolicy | None) -> None:
    level = policy.access_level if policy else ACCESS_LEVEL_PUBLIC
    setattr(dataset, "access_level", level)
    setattr(dataset, "is_password_protected", level == ACCESS_LEVEL_PASSWORD_PROTECTED)

def attach_access_levels(db: Session, datasets: Iterable[Dataset]) -> None:
    dataset_list = list(datasets)
    if not dataset_list:
        return
    dataset_ids = [d.id for d in dataset_list]
    rows = db.query(DatasetAccessPolicy).filter(DatasetAccessPolicy.dataset_id.in_(dataset_ids)).all()
    policy_map = {row.dataset_id: row for row in rows}
    for ds in dataset_list:
        attach_access_level(ds, policy_map.get(ds.id))"""

new_str = """def attach_access_level(dataset: Dataset, policy: DatasetAccessPolicy | None, include_password: bool = False) -> None:
    level = policy.access_level if policy else ACCESS_LEVEL_PUBLIC
    setattr(dataset, "access_level", level)
    setattr(dataset, "is_password_protected", level == ACCESS_LEVEL_PASSWORD_PROTECTED)
    if include_password and policy and level == ACCESS_LEVEL_PASSWORD_PROTECTED:
        if policy.password_hash and not policy.password_hash.startswith("$2b$"):
            setattr(dataset, "access_password", policy.password_hash)
        else:
            setattr(dataset, "access_password", "")
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
        attach_access_level(ds, policy_map.get(ds.id), include_password=include_password)"""

content = content.replace(old_str, new_str)
with open('/home/zy/zhangyi/rxncommons/backend/app/core/dataset_access.py', 'w') as f:
    f.write(content)
