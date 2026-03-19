import re

f_path = "/home/zy/zhangyi/rxncommons/backend/app/api/v1/endpoints/admin.py"
with open(f_path, "r", encoding="utf-8") as f:
    c = f.read()

old_logic = """    if visibility_filter == "public_visible":
        base_query = base_query.filter(
            Dataset.dataset_status == "published",
            ~protected_exists,
        )
    elif visibility_filter == "password_protected":
        base_query = base_query.filter(protected_exists)
    elif visibility_filter == "hidden_from_public":
        base_query = base_query.filter(
            or_(
                Dataset.dataset_status != "published",
                protected_exists,
            )
        )"""

new_logic = """    if visibility_filter == "public_visible":
        base_query = base_query.filter(~protected_exists)
    elif visibility_filter == "password_protected":
        base_query = base_query.filter(protected_exists)"""

c = c.replace(old_logic, new_logic)

with open(f_path, "w", encoding="utf-8") as f:
    f.write(c)

print("BACKEND FIXED")
