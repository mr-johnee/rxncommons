import re

file_path = "/home/zy/zhangyi/rxncommons/frontend/src/app/page.tsx"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Define the old block to match exactly starting from the buttons div to the scroll indicator
old_block_regex = re.compile(
    r'(<div className="mt-10 flex w-full flex-col items-center justify-center.*?gap-4 sm:w-auto sm:flex-row">.*?</button>)', 
    re.DOTALL
)

new_block = """          <form
            onSubmit={(e) => {
              e.preventDefault();
              const q = (e.target as any).q.value;
              window.location.href = `/datasets?search=${encodeURIComponent(q)}`;
            }}
            className="mx-auto mt-12 flex w-full max-w-2xl flex-col items-center"
          >
            <div className="relative flex w-full flex-col shadow-lg sm:flex-row overflow-hidden rounded-full bg-white ring-1 ring-border/20 focus-within:ring-2 focus-within:ring-primary/30 transition-shadow">
              <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-6">
                <Search className="h-5 w-5 text-muted-foreground/50" aria-hidden="true" />
              </div>
              <input
                name="q"
                type="text"
                autoComplete="off"
                className="block w-full border-none bg-transparent py-5 pl-14 pr-4 sm:pr-32 text-foreground placeholder:text-muted-foreground/70 focus:ring-0 text-base outline-none"
                placeholder="搜索感兴趣的数据、靶点或文章..."
              />
              <button
                type="submit"
                className="hidden sm:inline-flex absolute right-1.5 top-1.5 bottom-1.5 rounded-full bg-primary px-8 items-center text-sm font-semibold text-primary-foreground hover:bg-primary/95 transition-all shadow-sm active:scale-95"
              >
                探索数据
              </button>
            </div>
            {/* Mobile Submit */}
            <button
                type="submit"
                className="sm:hidden mt-4 w-full rounded-full bg-primary py-3.5 text-base font-semibold text-primary-foreground hover:bg-primary/95 transition-all shadow-sm active:scale-95"
            >
              探索数据
            </button>
          </form>

          <div className="mt-8 flex w-full flex-col items-center justify-center gap-4 sm:flex-row">
            <Link
              href="/datasets"
              className="w-full sm:w-auto text-center rounded-full bg-secondary/80 px-8 py-3 text-sm font-medium text-secondary-foreground shadow-sm transition-all hover:bg-secondary hover:shadow hover:-translate-y-0.5"
            >
              浏览全部数据集
            </Link>
            {user?.role === 'admin' ? (
              <Link href="/admin" className="group flex w-full items-center justify-center gap-2 rounded-full border border-border bg-white px-8 py-3 text-sm font-medium text-foreground shadow-sm transition-all hover:bg-muted/50 hover:text-primary sm:w-auto hover:-translate-y-0.5">
                进入管理后台 <span aria-hidden="true" className="transition-transform group-hover:translate-x-1">→</span>
              </Link>
            ) : (
              <Link href="/upload" className="group flex w-full items-center justify-center gap-2 rounded-full border border-border bg-white px-8 py-3 text-sm font-medium text-foreground shadow-sm transition-all hover:bg-muted/50 hover:text-primary sm:w-auto hover:-translate-y-0.5">
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
            className="group mt-14 inline-flex h-14 w-14 items-center justify-center rounded-full border border-white/60 bg-white/60 hover:bg-white hover:border-slate-200/80 shadow-sm hover:shadow-md backdrop-blur-md transition-all duration-300 text-slate-400 hover:text-primary active:scale-95"
          >
            <ChevronsDown className="h-6 w-6 animate-bounce pointer-events-none" style={{ animationDuration: '2.5s' }} />
          </button>"""

match = old_block_regex.search(content)
if match:
    content = content[:match.start()] + new_block + content[match.end():]
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("PATCH APPLIED!")
else:
    print("REGEX DID NOT MATCH!")
