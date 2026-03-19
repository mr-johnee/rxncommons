with open("/home/zy/zhangyi/rxncommons/frontend/src/app/admin/review-requests/[id]/page.tsx", "r", encoding="utf-8") as f:
    text = f.read()

# Make sure clock is imported cleanly.
text = text.replace("Clock3,", "Clock3,\n  Clock,")
text = text.replace("Clock3,\n  Clock,\n  Clock,", "Clock3,\n  Clock,")

with open("/home/zy/zhangyi/rxncommons/frontend/src/app/admin/review-requests/[id]/page.tsx", "w", encoding="utf-8") as f:
    f.write(text)
