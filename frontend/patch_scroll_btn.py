import re

file_path = "/home/zy/zhangyi/rxncommons/frontend/src/app/page.tsx"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

old_block = """          <div className="mt-8 inline-flex items-center gap-2 rounded-full border border-slate-200/80 bg-white/80 px-4 py-2 text-xs font-medium text-slate-600 shadow-sm backdrop-blur">
            <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-slate-100">
              <ChevronsDown className="h-3.5 w-3.5 text-slate-500" />
            </span>
            下滑查看下一模块
          </div>"""

new_block = """          <button 
            type="button"
            onClick={(e) => {
              e.preventDefault();
              document.querySelector('[data-section-index="1"]')?.scrollIntoView({ behavior: 'smooth' });
            }}
            className="group mt-14 inline-flex items-center gap-2.5 rounded-full border border-white/40 bg-white/50 hover:bg-white/90 hover:border-slate-200/70 px-6 py-3 text-sm font-medium text-slate-600 shadow-sm hover:shadow backdrop-blur-md transition-all duration-300"
          >
            下滑查看下一模块
            <span className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-white shadow-sm ring-1 ring-slate-100 group-hover:bg-primary/10 group-hover:ring-primary/20 transition-all">
              <ChevronsDown className="h-4 w-4 text-slate-400 group-hover:text-primary animate-bounce pointer-events-none" style={{ animationDuration: '2.5s' }} />
            </span>
          </button>"""

if old_block in content:
    content = content.replace(old_block, new_block)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("PATCH APPLIED!")
else:
    print("NOT FOUND!")
