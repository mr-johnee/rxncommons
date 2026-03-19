import re
with open('/home/zy/zhangyi/rxncommons/frontend/src/app/datasets/[id]/page.tsx', 'r') as f:
    content = f.read()

# Only show '去修改' if not draft, or if it is draft, another button has '继续当前草稿'.
# Actually '去修改' is effectively the same as continuing edit. Let's fix that.
content = re.sub(
    r"\{showManageButtons && \(dataset\.dataset_status === 'revision_required' \|\| inProgressVersion\?\.status === 'revision_required' \|\| inProgressVersion\?\.status === 'draft'\) && \(",
    r"{showManageButtons && (dataset.dataset_status === 'revision_required' || inProgressVersion?.status === 'revision_required') && (",
    content
)

with open('/home/zy/zhangyi/rxncommons/frontend/src/app/datasets/[id]/page.tsx', 'w') as f:
    f.write(content)
