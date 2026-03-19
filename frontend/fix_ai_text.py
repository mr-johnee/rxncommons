import re

file_home = "/home/zy/zhangyi/rxncommons/frontend/src/app/page.tsx"
with open(file_home, "r", encoding="utf-8") as f:
    h_content = f.read()

updates = [
    (
        "开箱即用的 AI 友好支撑", 
        "无缝衔接化学计算与 AI"
    ),
    (
        "面向计算与 AI 团队：清洗后的多模态结构化数据可无缝对接到下游机器学习模型训练中，极大降低特征工程成本，加速材料发现。", 
        "面向计算及 AI 团队：高标准解析的反应 SMILES 与规范的实验条件可被机器高效读取，极大降低预处理成本，加速产率预测与逆合成等模型的研发。"
    )
]

for old_t, new_t in updates:
    if old_t in h_content:
        h_content = h_content.replace(old_t, new_t)
    else:
        print(f"Warning: Could not find '{old_t}'")

with open(file_home, "w", encoding="utf-8") as f:
    f.write(h_content)

print("AI TEXT FIXED")
