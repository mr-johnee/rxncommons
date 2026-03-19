import re

file_path = '/home/zy/zhangyi/rxncommons/frontend/src/app/page.tsx'
with open(file_path, 'r') as f:
    text = f.read()

replacements = {
    # Desktop
    "打破文献附录与本地硬盘的数据孤岛，将零散的化学反应数据沉淀于同一平台，提供高效的一站式检索引擎与下载通道。": "打破异构文献补充材料与孤立环境的壁垒。汇聚多维化学反应数据，提供基于统一标准的强健检索引擎与批处理通道。",
    
    "支持对数据集核心指标进行深度刻画。透明化的全维度特征展示，极大降低背景缺失带来的不确定性，提高后续复用效率。": "倡导严密的实验条件和特征声明。通过透明化的体系刻画与要素补全，扫除因背景信息缺失造成的复现盲区，提升数据的学术复用价值。",
    
    "融合灵活的受控共享方案与严谨的版本溯源树。每一次修订均被完整追踪，实现权限粒度精细控制，构建安全科研生态。": "建立科学的读写权限分层与同行审核流程。依托具备强致密性的版本迭代树，保障科学数据的动态演进具有极高的学术公信力。"
}

for old, new in replacements.items():
    text = text.replace(old, new)

with open(file_path, 'w') as f:
    f.write(text)

print("Text updated successfully.")
