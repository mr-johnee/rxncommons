import re
with open('/home/zy/zhangyi/rxncommons/frontend/src/app/profile/page.tsx', 'r') as f:
    content = f.read()

content = re.sub(
    r"\{\(ds\.dataset_status === 'draft' \|\| ds\.dataset_status === 'revision_required'\) \? '继续编辑' : '查看'\}",
    r"{(ds.dataset_status === 'draft' || ds.dataset_status === 'revision_required') ? (ds.current_version && Number(ds.current_version) > 0 ? '管理' : '继续编辑') : '查看'}",
    content
)

with open('/home/zy/zhangyi/rxncommons/frontend/src/app/profile/page.tsx', 'w') as f:
    f.write(content)
