import re

# 1. FIX TOGGLE CENTERING IN PROFILE PAGE
file_profile = "/home/zy/zhangyi/rxncommons/frontend/src/app/profile/page.tsx"
with open(file_profile, "r", encoding="utf-8") as f:
    p_content = f.read()

# Replace the text span blocks in the toggle
old_toggle_spans = r"""                        <span className={`absolute right-1 text-[10px] font-bold text-white transition-opacity duration-300 w-[24px] text-center ${ds.access_level === 'password_protected' ? 'opacity-0' : 'opacity-100'}`} style={{ top: '50%', transform: 'translateY(-50%)' }}>
                          公开
                        </span>
                        
                        <span className={`absolute left-1 text-[10px] font-bold text-white transition-opacity duration-300 w-[24px] text-center ${ds.access_level === 'password_protected' ? 'opacity-100' : 'opacity-0'}`} style={{ top: '50%', transform: 'translateY(-50%)' }}>
                          私密
                        </span>"""

new_toggle_spans = """                        <span className={`absolute right-0 top-0 h-full w-[34px] flex items-center justify-center text-[10px] font-bold text-white transition-opacity duration-300 ${ds.access_level === 'password_protected' ? 'opacity-0' : 'opacity-100'}`}>
                          公开
                        </span>
                        
                        <span className={`absolute left-0 top-0 h-full w-[34px] flex items-center justify-center text-[10px] font-bold text-white transition-opacity duration-300 ${ds.access_level === 'password_protected' ? 'opacity-100' : 'opacity-0'}`}>
                          私密
                        </span>"""

if old_toggle_spans in p_content:
    p_content = p_content.replace(old_toggle_spans, new_toggle_spans)
else:
    print("WARNING: Toggle spans not found in profile")

with open(file_profile, "w", encoding="utf-8") as f:
    f.write(p_content)

# 2. FIX TEXTS IN HOME PAGE
file_home = "/home/zy/zhangyi/rxncommons/frontend/src/app/page.tsx"
with open(file_home, "r", encoding="utf-8") as f:
    h_content = f.read()

# Make sure we replace mobile and desktop versions
updates = [
    # Feature 1
    ("一站式标准化数据获取", "集中化的一站式数据查阅"),
    ("面向化学从业者：基于统一 Schema 对反应数据进行结构化沉淀，消除设备与团队间的数据孤岛，大幅提升数据检索与复用率。", "打破文献附录与本地硬盘的数据孤岛，将零散的化学反应数据集中沉淀，面向研究者提供便捷的一站式查阅、检索与下载体验。"),
    
    # Feature 2
    ("精细化资产池与版本管控", "高标准的化学数据规范化"),
    ("面向数据管理者：支持按需切换数据集的公开或私密状态，提供精准的受控共享方案，并通过严格版本管理保护核心数据脉络。", "告别格式与标准混乱的原始文件。基于统一的 Schema 对多来源化学数据进行结构化建模与清洗，让实验记录严谨清晰，极大提升复用效率。"),
    
    # Feature 3
    ("无缝衔接化学计算与 AI", "精细化的权限与版本管理"),
    ("面向计算及 AI 团队：高标准解析的反应 SMILES 与规范的实验条件可被机器高效读取，极大降低预处理成本，加速产率预测与逆合成等模型的研发。", "提供灵活的「公开/私密」状态切换实现数据受控共享；同时内置严格的迭代溯源机制，完整追踪每一次数据集修订，全方位保护核心科研资产。")
]

for old_t, new_t in updates:
    if old_t in h_content:
        h_content = h_content.replace(old_t, new_t)
    else:
        print(f"WARNING: Text not found in home: {old_t}")

with open(file_home, "w", encoding="utf-8") as f:
    f.write(h_content)

print("ALL CHANGES COMPLETED")
