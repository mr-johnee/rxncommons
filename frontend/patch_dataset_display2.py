import re
with open('/home/zy/zhangyi/rxncommons/frontend/src/app/datasets/[id]/page.tsx', 'r') as f:
    content = f.read()

# Replace `dataset.dataset_status === 'published' || dataset.dataset_status === 'revision_required'` with check for in_progress
content = re.sub(
    r"\{showManageButtons && \(dataset\.dataset_status === 'published' \|\| dataset\.dataset_status === 'revision_required'\) && !inProgressVersion && \(",
    r"{showManageButtons && (dataset.dataset_status === 'published' || dataset.dataset_status === 'revision_required') && !inProgressVersion && (",
    content
)

# wait, the displayStatus calculation 
content = re.sub(
    r"dataset\.dataset_status === 'pending_review' \|\| dataset\.dataset_status === 'draft' \|\| dataset\.dataset_status === 'revision_required'",
    r"dataset.dataset_status === 'pending_review' || dataset.dataset_status === 'draft' || dataset.dataset_status === 'revision_required'",
    content
)


with open('/home/zy/zhangyi/rxncommons/frontend/src/app/datasets/[id]/page.tsx', 'w') as f:
    f.write(content)
