with open("/home/zy/zhangyi/rxncommons/backend/app/api/v1/endpoints/admin.py", "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace("from sqlalchemy import or_", "from sqlalchemy import or_, and_")

with open("/home/zy/zhangyi/rxncommons/backend/app/api/v1/endpoints/admin.py", "w", encoding="utf-8") as f:
    f.write(text)
print("Fixed admin.py imports")
