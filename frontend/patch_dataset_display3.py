import re
with open('/home/zy/zhangyi/rxncommons/frontend/src/app/datasets/[id]/page.tsx', 'r') as f:
    content = f.read()

# Replace condition for revision_required button
content = re.sub(
    r"\{showManageButtons && \(dataset\.dataset_status === 'revision_required' \|\| inProgressVersion\?\.status === 'revision_required'\) && \(",
    r"{showManageButtons && (dataset.dataset_status === 'revision_required' || inProgressVersion?.status === 'revision_required' || inProgressVersion?.status === 'draft') && (",
    content
)

with open('/home/zy/zhangyi/rxncommons/frontend/src/app/datasets/[id]/page.tsx', 'w') as f:
    f.write(content)
