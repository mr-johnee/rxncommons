import re
with open('/home/zy/zhangyi/rxncommons/frontend/src/app/datasets/[id]/page.tsx', 'r') as f:
    content = f.read()

# Make sure submit review checks if there's any published version and keeps the label as "管理" maybe? Wait, profile handles this.
# Let's ensure display status behaves correctly if a draft is just pending.
pass
