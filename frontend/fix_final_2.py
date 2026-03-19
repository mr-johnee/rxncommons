import re

file_profile = "/home/zy/zhangyi/rxncommons/frontend/src/app/profile/page.tsx"
with open(file_profile, "r", encoding="utf-8") as f:
    p_content = f.read()

# 1. TABLE HEADER AND CELL CENTER ALIGNMENT
p_content = p_content.replace('<th className="p-4">状态</th>', '<th className="p-4 text-center border-l border-r border-transparent">状态</th>')
p_content = p_content.replace('<td className="p-4">\n                    <div className="flex items-center gap-2">', '<td className="p-4 align-middle">\n                    <div className="flex items-center justify-center gap-2">')

# 2. FIX TOGGLE DESIGN (Smaller, texts centered vertically, perfectly aligned)
old_toggle = r"""                      <button
                        onClick={(e) => { e.preventDefault(); handleTogglePrivacy(ds); }}
                        className={`relative inline-flex h-7 w-[72px] shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors duration-300 ease-in-out focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 ${
                          ds.access_level === 'password_protected' ? 'bg-amber-500' : 'bg-emerald-500'
                        }`}
                        role="switch"
                        title={ds.access_level === 'password_protected' ? "当前：私密。点击设为公开" : "当前：公开。点击设为私密"}
                      >
                        <span className="sr-only">切换可见度</span>
                        
                        <span className={`absolute right-2 text-[11px] font-bold text-white transition-opacity duration-300 ${ds.access_level === 'password_protected' ? 'opacity-0' : 'opacity-100'}`}>
                          公开
                        </span>
                        
                        <span className={`absolute left-2 text-[11px] font-bold text-white transition-opacity duration-300 ${ds.access_level === 'password_protected' ? 'opacity-100' : 'opacity-0'}`}>
                          私密
                        </span>
                        
                        <span
                          className={`pointer-events-none z-10 flex h-6 w-6 transform items-center justify-center rounded-full bg-white shadow-md ring-0 transition-transform duration-300 ease-in-out`}
                          style={{ transform: ds.access_level === 'password_protected' ? 'translateX(44px)' : 'translateX(0px)' }}
                        >
                          {ds.access_level === 'password_protected' ? (
                            <Lock className="h-3.5 w-3.5 text-amber-500" />
                          ) : (
                            <Globe2 className="h-3.5 w-3.5 text-emerald-500" />
                          )}
                        </span>
                      </button>"""

new_toggle = """                      <button
                        onClick={(e) => { e.preventDefault(); handleTogglePrivacy(ds); }}
                        className={`relative inline-flex h-6 w-14 shrink-0 cursor-pointer items-center rounded-full border border-transparent transition-colors duration-300 ease-in-out focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 ${
                          ds.access_level === 'password_protected' ? 'bg-amber-500' : 'bg-emerald-500'
                        }`}
                        role="switch"
                        title={ds.access_level === 'password_protected' ? "当前：私密。点击设为公开" : "当前：公开。点击设为私密"}
                      >
                        <span className="sr-only">切换可见度</span>
                        
                        <span className={`absolute right-1 text-[10px] font-bold text-white transition-opacity duration-300 w-[24px] text-center ${ds.access_level === 'password_protected' ? 'opacity-0' : 'opacity-100'}`} style={{ top: '50%', transform: 'translateY(-50%)' }}>
                          公开
                        </span>
                        
                        <span className={`absolute left-1 text-[10px] font-bold text-white transition-opacity duration-300 w-[24px] text-center ${ds.access_level === 'password_protected' ? 'opacity-100' : 'opacity-0'}`} style={{ top: '50%', transform: 'translateY(-50%)' }}>
                          私密
                        </span>
                        
                        <span
                          className={`pointer-events-none z-10 flex h-[20px] w-[20px] transform items-center justify-center rounded-full bg-white shadow-sm ring-0 transition-transform duration-300 ease-in-out`}
                          style={{ transform: ds.access_level === 'password_protected' ? 'translateX(34px)' : 'translateX(0px)' }}
                        >
                          {ds.access_level === 'password_protected' ? (
                            <Lock className="h-3 w-3 text-amber-500" />
                          ) : (
                            <Globe2 className="h-3 w-3 text-emerald-500" />
                          )}
                        </span>
                      </button>"""

p_content = p_content.replace(old_toggle, new_toggle)

# 3. FIX FILTER BUTTONS (Remove '所有' option, make the two buttons act as toggles that can be unselected)
old_filter = r"""          <div className="flex items-center bg-muted/50 p-1 rounded-lg border border-border">
            <button
              onClick={() => setPrivacyFilter('all')}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${privacyFilter === 'all' ? 'bg-background text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}
            >
              所有可见度
            </button>
            <button
              onClick={() => setPrivacyFilter('public')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${privacyFilter === 'public' ? 'bg-background text-emerald-600 shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}
            >
              <Globe2 className="w-3.5 h-3.5" />
              公开
            </button>
            <button
              onClick={() => setPrivacyFilter('password_protected')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${privacyFilter === 'password_protected' ? 'bg-background text-amber-600 shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}
            >
              <Lock className="w-3.5 h-3.5" />
              私密
            </button>
          </div>"""

new_filter = """          <div className="flex items-center gap-2">
            <button
              onClick={() => setPrivacyFilter(privacyFilter === 'public' ? 'all' : 'public')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md border text-xs font-medium transition-all ${privacyFilter === 'public' ? 'bg-emerald-50 border-emerald-200 text-emerald-700 shadow-sm' : 'bg-background border-input text-muted-foreground hover:bg-accent'}`}
            >
              <Globe2 className="w-3.5 h-3.5" />
              仅看公开
            </button>
            <button
              onClick={() => setPrivacyFilter(privacyFilter === 'password_protected' ? 'all' : 'password_protected')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md border text-xs font-medium transition-all ${privacyFilter === 'password_protected' ? 'bg-amber-50 border-amber-200 text-amber-700 shadow-sm' : 'bg-background border-input text-muted-foreground hover:bg-accent'}`}
            >
              <Lock className="w-3.5 h-3.5" />
              仅看私密
            </button>
          </div>"""

p_content = p_content.replace(old_filter, new_filter)

with open(file_profile, "w", encoding="utf-8") as f:
    f.write(p_content)


file_home = "/home/zy/zhangyi/rxncommons/frontend/src/app/page.tsx"
with open(file_home, "r", encoding="utf-8") as f:
    h_content = f.read()

# 4. FIX HOME PAGE TEXTS (3 Characteristics Optimization)
features_updates = [
    (
        "灵活的访问与可见度管控", 
        "一站式标准化数据获取"
    ),
    (
        "支持按需切换数据集的公开与私密状态，提供精准的受控共享方案，保护核心数据资产。", 
        "面向化学从业者：基于统一 Schema 对反应数据进行结构化沉淀，消除设备与团队间的数据孤岛，大幅提升数据检索与复用率。"
    ),
    (
        "统一的标准化数据接口", 
        "精细化资产池与版本管控"
    ),
    (
        "基于统一Schema对化学数据进行结构化建模，消除设备与团队间的数据孤岛，提升数据复用率。", 
        "面向数据管理者：支持按需切换数据集的公开或私密状态，提供精准的受控共享方案，并通过严格版本管理保护核心数据脉络。"
    ),
    (
        "面向AI驱动的特征工程", 
        "开箱即用的 AI 友好支撑"
    ),
    (
        "系统沉淀的数据可无缝对接到下游机器学习流水线，极大降低清洗成本，加速AI辅助材料发现。", 
        "面向计算与 AI 团队：清洗后的多模态结构化数据可无缝对接到下游机器学习模型训练中，极大降低特征工程成本，加速材料发现。"
    )
]

for old_t, new_t in features_updates:
    h_content = h_content.replace(old_t, new_t)

with open(file_home, "w", encoding="utf-8") as f:
    f.write(h_content)

print("ALL FIXES SCRIPTS COMPLETED")
