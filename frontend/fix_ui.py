import re

# 1. FIX page.tsx TEXTS
file_home = "/home/zy/zhangyi/rxncommons/frontend/src/app/page.tsx"
with open(file_home, "r", encoding="utf-8") as f:
    h_content = f.read()

# Pattern to replace section texts
updates = [
    ("深度适配化学科研场景", "精细化管理科研数据资产"),
    ("不仅仅是简单的文件存储，RxnCommons 对化学数据的上下文进行了深度建模与解析。", "不止于简单的文件存储，RxnCommons 提供了从数据收集、多级审核、版本管控到安全共享的完整生命周期管理。"),
    ("原生化学格式支持", "灵活的访问与可见度管控"),
    ("除通用 CSV/XLSX 外，支持 reaction SMILES 解析与基础合法性检查。", "支持按需切换数据集的公开与私密状态，提供精准的受控共享方案，保护核心数据资产。"),
    ("精确化学检索", "规范的协同与审核流转"),
    ("通过标签与字段语义快速筛选有价值的数据子集，减少无效检索。", "内置草稿提交、平台审核、多状态追踪工作流，通过严格的数据质量把关沉淀高可用科研数据。"),
    ("可信版本溯源", "可追溯的数据版本管理"),
    ("每次迭代均有可追溯记录，便于复现实验并沉淀长期可用的数据资产。", "所有数据集变更均会产生独立更新记录与版本号，保留完整发布脉络，为团队实验溯源提供坚实依据。")
]

for old_str, new_str in updates:
    h_content = h_content.replace(old_str, new_str)

with open(file_home, "w", encoding="utf-8") as f:
    f.write(h_content)
    
print("HOME TEXTS FIXED")

# 2. FIX profile UI
file_profile = "/home/zy/zhangyi/rxncommons/frontend/src/app/profile/page.tsx"
with open(file_profile, "r", encoding="utf-8") as f:
    p_content = f.read()

old_button_block = r"""                      {ds.access_level === 'password_protected' ? (
                        <button onClick={(e) => { e.preventDefault(); handleTogglePrivacy(ds); }} title="目前为私密，点击可设为公开" className="flex items-center gap-1 px-2 py-1 rounded text-xs font-medium bg-amber-50 text-amber-600 border border-amber-200/50 hover:bg-amber-100 hover:text-amber-700 transition-colors">
                          <Lock className="w-3 h-3" />
                          私密
                        </button>
                      ) : (
                        <button onClick={(e) => { e.preventDefault(); handleTogglePrivacy(ds); }} title="目前为公开，点击可设为私密" className="flex items-center gap-1 px-2 py-1 rounded text-xs font-medium bg-emerald-50 text-emerald-600 border border-emerald-200/50 hover:bg-emerald-100 hover:text-emerald-700 transition-colors">
                          <Globe2 className="w-3 h-3" />
                          公开
                        </button>
                      )}"""

new_button_block = """                      <button
                        onClick={(e) => { e.preventDefault(); handleTogglePrivacy(ds); }}
                        className={`relative inline-flex h-6 w-14 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 ${
                          ds.access_level === 'password_protected' ? 'bg-amber-500' : 'bg-emerald-500'
                        }`}
                        role="switch"
                        title={ds.access_level === 'password_protected' ? "当前：私密。点击设为公开" : "当前：公开。点击设为私密"}
                      >
                        <span className="sr-only">切换可见度</span>
                        <span className={`absolute left-1 text-[10px] font-bold text-white transition-opacity duration-200 ${ds.access_level === 'password_protected' ? 'opacity-0' : 'opacity-100'}`}>
                          公开
                        </span>
                        <span className={`absolute right-1 text-[10px] font-bold text-white transition-opacity duration-200 ${ds.access_level === 'password_protected' ? 'opacity-100' : 'opacity-0'}`}>
                          私密
                        </span>
                        <span
                          className={`pointer-events-none z-10 flex h-[20px] w-[20px] transform items-center justify-center rounded-full bg-white shadow-sm ring-0 transition-transform duration-200 ease-in-out ${
                            ds.access_level === 'password_protected' ? 'translate-x-[32px]' : 'translate-x-0'
                          }`}
                        >
                          {ds.access_level === 'password_protected' ? (
                            <Lock className="h-3 w-3 text-amber-500" />
                          ) : (
                            <Globe2 className="h-[11px] w-[11px] text-emerald-500" />
                          )}
                        </span>
                      </button>"""

if old_button_block in p_content:
    p_content = p_content.replace(old_button_block, new_button_block)
else:
    print("PROFILE OLD BUTTON BLOCK NOT FOUND")

# Also add an alert feedback to handleTogglePrivacy
old_try_block = r"""    try {
      const payload: any = { access_level: isPrivate ? 'public' : 'password_protected' };
      if (!isPrivate) {
         payload.access_password = ds.access_password || Math.random().toString(36).slice(-8);
      }
      const res = await api.put(`/datasets/${ds.id}/access-policy`, payload);
      setDatasets((prev) => prev.map((item: any) => 
        item.id === ds.id ? { ...item, access_level: res.data?.access_level, access_password: payload.access_password || item.access_password } : item
      ));
    } catch (err: any) {"""

new_try_block = """    try {
      const payload: any = { access_level: isPrivate ? 'public' : 'password_protected' };
      if (!isPrivate) {
         payload.access_password = ds.access_password || Math.random().toString(36).slice(-8);
      }
      const res = await api.put(`/datasets/${ds.id}/access-policy`, payload);
      setDatasets((prev) => prev.map((item: any) => 
        item.id === ds.id ? { ...item, access_level: res.data?.access_level, access_password: payload.access_password || item.access_password } : item
      ));
      
      // 显示状态刷新成功提示
      // 如果当前使用了筛选器，自动从当前视图消失时给予明确提示
      if (privacyFilter !== 'all') {
         alert(`操作成功！数据集已转为 ${actionName}。\\n(由于当前处于筛选视图，该数据集可能会从列表中隐藏)`);
      }
    } catch (err: any) {"""

if old_try_block in p_content:
    p_content = p_content.replace(old_try_block, new_try_block)
else:
    print("PROFILE TRY BLOCK NOT FOUND")

with open(file_profile, "w", encoding="utf-8") as f:
    f.write(p_content)

print("PROFILE BOTH CHANGES APPLIED")

