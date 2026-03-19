with open("/home/zy/zhangyi/rxncommons/frontend/src/app/admin/page.tsx", "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace("<Clock ", "<Clock3 ")

with open("/home/zy/zhangyi/rxncommons/frontend/src/app/admin/page.tsx", "w", encoding="utf-8") as f:
    f.write(text)
print("Fixed Clock import")
