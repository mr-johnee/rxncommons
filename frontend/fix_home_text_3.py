import re

file_home = "/home/zy/zhangyi/rxncommons/frontend/src/app/page.tsx"
with open(file_home, "r", encoding="utf-8") as f:
    h_content = f.read()

old_t = "告别格式与标准混乱的原始文件。基于统一的 Schema 对多来源化学数据进行结构化建模与清洗，让实验记录严谨清晰，极大提升复用效率。"
new_t = "告别因背景信息缺失而导致的复用难题。平台强力支持对数据集的元数据及其各字段含义进行详尽的刻画与说明，让每一条数据语境都清晰可溯，极大降低后续使用的门槛。"

count = h_content.count(old_t)
print(f"Found {count} instances")

h_content = h_content.replace(old_t, new_t)

with open(file_home, "w", encoding="utf-8") as f:
    f.write(h_content)

print("HOME TEXT 3 FIXED")
