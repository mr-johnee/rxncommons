import re

file_home = "/home/zy/zhangyi/rxncommons/frontend/src/app/page.tsx"
with open(file_home, "r", encoding="utf-8") as f:
    h_content = f.read()

# Replace using regex to handle whitespace/newlines
pattern = r"告别格式与标准混乱的原始文件。基于统一的 Schema 对多来源化学数据.*?极大提升复用效率。"
new_t = "告别因缺少背景信息而导致的复用难题。平台要求并支持对数据集元数据及字段含义进行详尽说明，让每条记录语境都清晰可溯，极大降低用户理解与使用门槛。"

h_content, count = re.subn(pattern, new_t, h_content, flags=re.DOTALL)
print(f"Replaced {count} instances")

with open(file_home, "w", encoding="utf-8") as f:
    f.write(h_content)

