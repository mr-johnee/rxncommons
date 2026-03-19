import re
with open('/home/zy/zhangyi/rxncommons/backend/app/api/v1/endpoints/datasets.py', 'r') as f:
    content = f.read()

# Inside cancel_review
content = re.sub(
    r"dataset\.dataset_status = pending_req\.pre_review_status or \"draft\"",
    r"if dataset.dataset_status != 'published':\n        dataset.dataset_status = pending_req.pre_review_status or \"draft\"",
    content
)

with open('/home/zy/zhangyi/rxncommons/backend/app/api/v1/endpoints/datasets.py', 'w') as f:
    f.write(content)
