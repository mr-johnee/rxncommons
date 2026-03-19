import re

file_path = '/home/zy/zhangyi/rxncommons/backend/app/api/v1/endpoints/admin.py'
with open(file_path, 'r') as f:
    content = f.read()

old_logic = """    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if dataset.dataset_status not in PUBLIC_STATUSES:
        raise HTTPException(status_code=409, detail="dataset_status_not_public")"""

new_logic = """    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if dataset.dataset_status not in PUBLIC_STATUSES:
        raise HTTPException(status_code=409, detail="dataset_status_not_public")
    if dataset.is_password_protected or dataset.access_level == 'password_protected':
        raise HTTPException(status_code=409, detail="privacy_dataset_cannot_be_featured")"""

if old_logic in content:
    content = content.replace(old_logic, new_logic)
else:
    print("WARNING: Old logic not found in backend admin.py")

with open(file_path, 'w') as f:
    f.write(content)

