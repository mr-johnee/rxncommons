import re
with open('/home/zy/zhangyi/rxncommons/backend/app/api/v1/endpoints/admin.py', 'r') as f:
    content = f.read()

# Replace `dataset.dataset_status = "revision_required"` with conditional
content = re.sub(
    r"dataset\.dataset_status = \"revision_required\"",
    r"if dataset.dataset_status != 'published':\n        dataset.dataset_status = \"revision_required\"",
    content
)

with open('/home/zy/zhangyi/rxncommons/backend/app/api/v1/endpoints/admin.py', 'w') as f:
    f.write(content)
