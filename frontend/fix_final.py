import re

file_profile = "/home/zy/zhangyi/rxncommons/frontend/src/app/profile/page.tsx"
with open(file_profile, "r", encoding="utf-8") as f:
    p_content = f.read()

# 1. FIX TOGGLE UI in profile/page.tsx
old_toggle = r"""                      <button
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

new_toggle = """                      <button
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

p_content = p_content.replace(old_toggle, new_toggle)

# 2. FIX FILTER UI in profile/page.tsx
old_filter = r"""          <select 
            className="text-sm bg-background border border-input rounded-md px-2 py-1.5 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/20 text-foreground cursor-pointer"
            value={privacyFilter}
            onChange={(e) => setPrivacyFilter(e.target.value as any)}
          >
            <option value="all">所有可见度</option>
            <option value="public">🌐 公开</option>
            <option value="password_protected">🔒 私密</option>
          </select>"""

new_filter = """          <div className="flex items-center bg-muted/50 p-1 rounded-lg border border-border">
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

p_content = p_content.replace(old_filter, new_filter)

with open(file_profile, "w", encoding="utf-8") as f:
    f.write(p_content)


file_home = "/home/zy/zhangyi/rxncommons/frontend/src/app/page.tsx"
with open(file_home, "r", encoding="utf-8") as f:
    h_content = f.read()

# 3. ADD KEYBOARD LISTENER to page.tsx
old_scroll_useEffect = r"""    container.addEventListener('wheel', onWheel, { passive: false });
    return () => {
      container.removeEventListener('wheel', onWheel);
    };
  }, [user]);"""

new_scroll_useEffect = """    container.addEventListener('wheel', onWheel, { passive: false });
    
    // Keyboard navigation
    const onKeyDown = (event: KeyboardEvent) => {
      if (document.activeElement?.tagName === 'INPUT' || document.activeElement?.tagName === 'TEXTAREA') {
        return;
      }
      
      if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
        if (lockingRef.current) {
          event.preventDefault();
          return;
        }
        
        const sections = getSectionNodes();
        if (sections.length === 0) return;
        const currentIndex = getCurrentSectionIndex(sections);
        const targetIndex = event.key === 'ArrowDown'
          ? Math.min(sections.length - 1, currentIndex + 1)
          : Math.max(0, currentIndex - 1);
          
        if (targetIndex !== currentIndex) {
          event.preventDefault();
          scrollToSectionIndex(targetIndex);
        }
      }
    };
    window.addEventListener('keydown', onKeyDown, { passive: false });

    return () => {
      container.removeEventListener('wheel', onWheel);
      window.removeEventListener('keydown', onKeyDown);
    };
  }, [user]);"""

h_content = h_content.replace(old_scroll_useEffect, new_scroll_useEffect)

# 4. FIX HOME PAGE TEXTS
updates = [
    (
        "规范的协同与审核流转", 
        "统一的标准化数据接口"
    ),
    (
        "内置草稿提交、平台审核、多状态追踪工作流，通过严格的数据质量把关沉淀高可用科研数据。", 
        "基于统一Schema对化学数据进行结构化建模，消除设备与团队间的数据孤岛，提升数据复用率。"
    ),
    (
        "可追溯的数据版本管理", 
        "面向AI驱动的特征工程"
    ),
    (
        "所有数据集变更均会产生独立更新记录与版本号，保留完整发布脉络，为团队实验溯源提供坚实依据。", 
        "系统沉淀的数据可无缝对接到下游机器学习流水线，极大降低清洗成本，加速AI辅助材料发现。"
    )
]

for old_t, new_t in updates:
    h_content = h_content.replace(old_t, new_t)

with open(file_home, "w", encoding="utf-8") as f:
    f.write(h_content)

print("ALL FIXES SCRIPTS COMPLETED")
