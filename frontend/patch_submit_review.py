import re
with open('/home/zy/zhangyi/rxncommons/backend/app/api/v1/endpoints/datasets.py', 'r') as f:
    content = f.read()

# Replace `dataset.dataset_status = 'pending_review'` inside submit_review only if previously published.
# Wait, let's keep it simple: dataset_status reflects highest version status. If dataset_status is published, and we submit a review for draft, its dataset_status should STAY published. The version goes pending.
content = re.sub(
    r"pre_review_status = dataset\.dataset_status\n\s+dataset\.dataset_status = 'pending_review'\n\s+dataset\.status_reason = None\n\s+version\.status = 'pending_review'", 
    r"pre_review_status = dataset.dataset_status\n    if dataset.dataset_status != 'published':\n        dataset.dataset_status = 'pending_review'\n    dataset.status_reason = None\n    version.status = 'pending_review'", 
    content
)

with open('/home/zy/zhangyi/rxncommons/backend/app/api/v1/endpoints/datasets.py', 'w') as f:
    f.write(content)
