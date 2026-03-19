import re

file_page = "/home/zy/zhangyi/rxncommons/frontend/src/app/datasets/[id]/page.tsx"
with open(file_page, "r", encoding="utf-8") as f:
    content = f.read()

# Fix 1: line ~153
old_1 = "const canViewUnpublished = Boolean(user && (user.role === 'admin' || (isOwner && isManage)));"
new_1 = "const canViewUnpublished = Boolean(user && isManage && (user.role === 'admin' || isOwner));"
content = content.replace(old_1, new_1)

# Fix 2: line ~438
old_2 = "const canViewUnpublishedVersion = Boolean(user && (user.role === 'admin' || showManageButtons));"
new_2 = "const canViewUnpublishedVersion = Boolean(user && isManage && (user.role === 'admin' || isOwner));"
content = content.replace(old_2, new_2)

with open(file_page, "w", encoding="utf-8") as f:
    f.write(content)

print("ADMIN DATASET VERSIONS FIXED")
