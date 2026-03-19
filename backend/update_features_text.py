import re

file_path = '/home/zy/zhangyi/rxncommons/frontend/src/app/page.tsx'
with open(file_path, 'r') as f:
    text = f.read()

# Make the feature texts more rigorous and academic
replacements = {
    "精细化管理科研数据资产": "构建开放与严谨的科研基础设施",
    "不止于简单的文件存储，RxnCommons 提供了从数据收集、多级审核、版本管控到安全共享的完整生命周期管理。": "超越传统文件归档，为化学与数据科学交叉领域提供从严密标引、同行评议、版本迭代到安全分发的结构化治理方案。",
    
    # Mobile
    "集中化数据汇聚": "全局化学资源集成体系",
    "打破文献附录与本地硬盘的数据孤岛，将零散的化学反应数据沉淀于协作平台，提供高效的检索与下载通道。": "打破异构文献补充材料与孤立环境的壁垒。汇聚多维化学反应数据，提供基于统一标准的强健检索引擎与批处理通道。",
    
    "高标准数据规范": "多维度元数据标引规范",
    "透明化的全维度特征展示与元数据刻画，极大降低背景缺失带来的不确定性，成倍提升后续复用效率。": "倡导严密的实验条件和特征声明。通过透明化的体系刻画与要素补全，扫除因背景信息缺失造成的复现盲区，提升数据的学术复用价值。",
    
    "全方位资产托管": "版本追踪与受控共享机制",
    "提供灵活的受控共享方案与严谨的版本溯源树。每一次修订均被完整追踪，实现权限粒度精细控制。": "建立科学的读写权限分层与同行审核流程。依托具备强致密性的版本迭代树，保障科学数据的动态演进具有时间一致性与极高的学术公信力。"
}

for old, new in replacements.items():
    text = text.replace(old, new)

with open(file_path, 'w') as f:
    f.write(text)

print("Text updated successfully.")
