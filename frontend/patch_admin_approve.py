import re
with open('/home/zy/zhangyi/rxncommons/backend/app/api/v1/endpoints/admin.py', 'r') as f:
    content = f.read()

# Inside reject_review_request
content = re.sub(
    r"dataset\.dataset_status = req\.pre_review_status or \"draft\"",
    r"if dataset.dataset_status != 'published':\n        dataset.dataset_status = req.pre_review_status or \"draft\"",
    content
)

with open('/home/zy/zhangyi/rxncommons/backend/app/api/v1/endpoints/admin.py', 'w') as f:
    f.write(content)
