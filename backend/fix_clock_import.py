import re

with open("/home/zy/zhangyi/rxncommons/frontend/src/app/admin/review-requests/[id]/page.tsx", "r", encoding="utf-8") as f:
    text = f.read()

if "Clock," not in text and "\n  Clock," not in text and " Clock " not in text:
    text = text.replace("Clock3,", "Clock3,\n  Clock,")

with open("/home/zy/zhangyi/rxncommons/frontend/src/app/admin/review-requests/[id]/page.tsx", "w", encoding="utf-8") as f:
    f.write(text)
print("Added Clock import")
