import re
with open('/home/zy/zhangyi/rxncommons/frontend/src/app/datasets/[id]/page.tsx', 'r') as f:
    content = f.read()

# inProgressVersion is currently checking if status isn't published. Let's make it more robust. But first handle display version buttons
# No need to patch frontend display buttons heavily because dataset.dataset_status will now stay 'published' if there's a published v1.
# wait, if dataset.dataset_status remains 'published', what happen to 'inProgressVersion?.status == draft'?
# 'inProgressVersion' finds the highest unpublished version. If its status is 'pending_review', the 'cancel review' shouldn't just check 'dataset.dataset_status === 'pending_review''. It should check `inProgressVersion?.status === 'pending_review' || dataset.dataset_status === 'pending_review'`

content = re.sub(
    r"\{showManageButtons && dataset\.dataset_status === 'pending_review' && \(",
    r"{showManageButtons && (dataset.dataset_status === 'pending_review' || inProgressVersion?.status === 'pending_review') && (",
    content
)

content = re.sub(
    r"\{showManageButtons && dataset\.dataset_status === 'revision_required' && \(",
    r"{showManageButtons && (dataset.dataset_status === 'revision_required' || inProgressVersion?.status === 'revision_required') && (",
    content
)

with open('/home/zy/zhangyi/rxncommons/frontend/src/app/datasets/[id]/page.tsx', 'w') as f:
    f.write(content)
