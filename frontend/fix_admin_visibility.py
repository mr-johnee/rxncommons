import re

file_admin = "/home/zy/zhangyi/rxncommons/frontend/src/app/admin/page.tsx"
with open(file_admin, "r", encoding="utf-8") as f:
    content = f.read()

# Replace the dropdown HTML
old_select = r"""              <option value="all">全部可见性</option>
              <option value="public_visible">普通用户可见</option>
              <option value="password_protected">隐私数据集</option>
              <option value="hidden_from_public">普通用户不可见</option>"""

new_select = """              <option value="all">所有权限状态</option>
              <option value="public_visible">对外公开展示</option>
              <option value="password_protected">已设为私密 (密码保护)</option>"""

content = content.replace(old_select, new_select)

# We should also replace where it renders the tags in the list
old_tag_1 = "{ds.is_password_protected ? '隐私数据集' : '普通用户可见'}"
new_tag_1 = "{ds.is_password_protected ? '私密 (需口令)' : '公开展示'}"
content = content.replace(old_tag_1, new_tag_1)

# Also fix the `setVisibilityFilter(e.target.value as 'all' | ...)` typescript type
old_type = "setVisibilityFilter(e.target.value as 'all' | 'public_visible' | 'password_protected' | 'hidden_from_public');"
new_type = "setVisibilityFilter(e.target.value as 'all' | 'public_visible' | 'password_protected');"
content = content.replace(old_type, new_type)

with open(file_admin, "w", encoding="utf-8") as f:
    f.write(content)

print("ADMIN VISIBILITY SELECT OPTIONS FIXED")
