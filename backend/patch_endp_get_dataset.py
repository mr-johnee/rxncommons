import re

with open('/home/zy/zhangyi/rxncommons/backend/app/api/v1/endpoints/datasets.py', 'r') as f:
    content = f.read()

old_str = """    attach_access_level(dataset, get_dataset_access_policy(db, dataset.id))
    return dataset"""
new_str = """    is_owner_or_admin = bool(current_user and (current_user.role == "admin" or current_user.id == dataset.owner_id))
    attach_access_level(dataset, get_dataset_access_policy(db, dataset.id), include_password=is_owner_or_admin)
    return dataset"""

content = content.replace(old_str, new_str)

with open('/home/zy/zhangyi/rxncommons/backend/app/api/v1/endpoints/datasets.py', 'w') as f:
    f.write(content)
