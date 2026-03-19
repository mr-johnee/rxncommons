import re

file_path = "/home/zy/zhangyi/rxncommons/frontend/src/app/page.tsx"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Let's extract everything from '<p className="mt-6 text-lg' up to the start of '<section data-home-section="true" data-section-index="1"'
start_str = '          <p className="mt-6 text-lg leading-8 text-muted-foreground">'
end_str = '      {/* Part 2: Dataset Metrics + Featured */}'

start_idx = content.find(start_str)
end_idx = content.find(end_str)

if start_idx != -1 and end_idx != -1:
    old_section = content[start_idx:end_idx]
    
    new_section = r"""          <p className="mt-6 text-lg leading-8 text-muted-foreground">
            开放、可信、面向研究团队的可追溯数据发布与检索平台。
            <br className="hidden sm:inline" />
            连接全球化学研究者，加速科学发现。
          </p>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              const q = (e.target as any).q.value;
              window.location.href = `/datasets?search=${encodeURIComponent(q)}`;
            }}
            className="mx-auto mt-12 flex w-full max-w-2xl flex-col items-center"
          >
            <div className="relative flex w-full flex-col shadow sm:flex-row overflow-hidden rounded-full bg-white/90 backdrop-blur ring-1 ring-slate-200 focus-within:ring-2 focus-within:ring-primary/40 focus-within:shadow-md transition-all">
              <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-6">
                <Search className="h-5 w-5 text-slate-400" aria-hidden="true" />
              </div>
              <input
                name="q"
                type="text"
                autoComplete="off"
                className="block w-full border-none bg-transparent py-4 pl-14 pr-4 sm:pr-32 text-slate-800 placeholder:text-slate-400 focus:ring-0 text-base outline-none"
                placeholder="搜索感兴趣的数据、靶点或文章..."
              />
              <button
                type="submit"
                className="hidden sm:inline-flex absolute right-1.5 top-1.5 bottom-1.5 rounded-full bg-primary px-8 items-center text-sm font-medium text-primary-foreground hover:bg-primary/95 transition-all shadow-sm active:scale-95"
              >
                搜索
              </button>
            </div>
            {/* Mobile Submit */}
            <button
                type="submit"
                className="sm:hidden mt-4 w-full rounded-full bg-primary py-3.5 text-base font-medium text-primary-foreground hover:bg-primary/95 transition-all shadow-sm active:scale-95"
            >
              搜索
            </button>
          </form>

          <div className="mt-8 flex w-full flex-col items-center justify-center gap-4 sm:flex-row">
            <Link
              href="/datasets"
              className="w-full sm:w-auto text-center rounded-full bg-slate-100 px-8 py-3 text-sm font-medium text-slate-700 shadow-sm transition-all hover:bg-slate-200 hover:shadow hover:-translate-y-0.5"
            >
              浏览全部数据集
            </Link>
            {user?.role === 'admin' ? (
              <Link href="/admin" className="group flex w-full items-center justify-center gap-2 rounded-full border border-slate-200 bg-white px-8 py-3 text-sm font-medium text-slate-700 shadow-sm transition-all hover:bg-slate-50 hover:text-primary sm:w-auto hover:-translate-y-0.5">
                进入管理后台 <span aria-hidden="true" className="transition-transform group-hover:translate-x-1">→</span>
              </Link>
            ) : (
              <Link href="/upload" className="group flex w-full items-center justify-center gap-2 rounded-full border border-slate-200 bg-white px-8 py-3 text-sm font-medium text-slate-700 shadow-sm transition-all hover:bg-slate-50 hover:text-primary sm:w-auto hover:-translate-y-0.5">
                上传数据集 <span aria-hidden="true" className="transition-transform group-hover:translate-x-1">→</span>
              </Link>
            )}
          </div>

          <button 
            type="button"
            title="查看下一模块"
            onClick={(e) => {
              e.preventDefault();
              document.querySelector('[data-section-index="1"]')?.scrollIntoView({ behavior: 'smooth' });
            }}
            className="group mt-16 inline-flex h-12 w-12 items-center justify-center rounded-full border border-white/60 bg-white/50 hover:bg-white hover:border-slate-200/80 shadow-sm hover:shadow-md backdrop-blur-md transition-all duration-300 text-slate-400 hover:text-primary active:scale-95"
          >
            <ChevronsDown className="h-5 w-5 animate-bounce pointer-events-none" style={{ animationDuration: '2.5s' }} />
          </button>
        </div>
      </section>

"""
    content = content[:start_idx] + new_section + content[end_idx:]
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("PATCH APPLIED CLEANLY")
else:
    print("COULD NOT FIND BOUNDARIES")
