import re

with open('/home/zy/zhangyi/rxncommons/frontend/src/app/page.tsx', 'r') as f:
    content = f.read()

mobile_old = """                <Link
                  href="/datasets"
                  className="relative overflow-hidden group min-w-[220px] snap-start flex min-h-[220px] flex-col justify-between rounded-2xl bg-gradient-to-br from-primary to-primary/90 p-6 shadow-md transition-all hover:-translate-y-1 hover:shadow-xl"
                >
                  <div className="relative z-10">
                    <p className="text-xs font-medium tracking-widest text-primary-foreground/80">发现更多</p>
                    <h3 className="mt-2 text-2xl font-bold tracking-tight text-primary-foreground">全部数据集</h3>
                    <p className="mt-3 text-sm leading-relaxed text-primary-foreground/90">
                      浏览完整数据集列表，细致检索与筛选，快速定位你所需的优质数据。
                    </p>
                  </div>
                  <div className="relative z-10 mt-6 inline-flex w-fit items-center gap-2 rounded-full bg-white/20 px-4 py-2 text-sm font-semibold text-white backdrop-blur-md transition-colors group-hover:bg-white/30">
                    进入数据广场
                    <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                  </div>
                  <Database className="absolute -bottom-4 -right-4 h-24 w-24 text-white opacity-10 transition-transform duration-500 group-hover:scale-110 group-hover:opacity-20" aria-hidden="true" />
                </Link>"""

mobile_new = """                <Link
                  href="/datasets"
                  className="relative overflow-hidden group min-w-[220px] snap-start flex min-h-[220px] flex-col justify-between rounded-2xl bg-primary/5 border border-primary/20 p-6 shadow-sm transition-all hover:-translate-y-1 hover:shadow-md hover:bg-primary/10"
                >
                  <div className="relative z-10">
                    <div className="flex items-center gap-2 mb-2">
                        <Sparkles className="h-4 w-4 text-primary" />
                        <p className="text-xs font-medium tracking-widest text-primary">发现更多</p>
                    </div>
                    <h3 className="mt-2 text-2xl font-bold tracking-tight text-foreground">全部数据集</h3>
                    <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
                      浏览完整数据集列表，细致检索与筛选，快速定位你所需的优质数据。
                    </p>
                  </div>
                  <div className="relative z-10 mt-6 inline-flex w-fit items-center gap-2 rounded-full bg-primary/10 px-4 py-2 text-sm font-semibold text-primary transition-colors group-hover:bg-primary/20">
                    进入数据广场
                    <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                  </div>
                </Link>"""

desktop_old = """                <Link
                  href="/datasets"
                  className="relative overflow-hidden group mx-auto flex min-h-[220px] w-full max-w-[320px] flex-col justify-between rounded-2xl bg-gradient-to-br from-primary to-primary/90 p-6 shadow-md transition-all hover:-translate-y-1 hover:shadow-xl"
                >
                  <div className="relative z-10">
                    <p className="text-xs font-medium tracking-widest text-primary-foreground/80">发现更多</p>
                    <h3 className="mt-2 text-2xl font-bold tracking-tight text-primary-foreground">全部数据集</h3>
                    <p className="mt-3 text-sm leading-relaxed text-primary-foreground/90">
                      浏览完整数据集列表，细致筛选与检索，精准定位各类化学反应数据源。
                    </p>
                  </div>
                  <div className="relative z-10 mt-6 inline-flex w-fit items-center gap-2 rounded-full bg-white/20 px-4 py-2 text-sm font-semibold text-white backdrop-blur-md transition-colors group-hover:bg-white/30">
                    前往广场探索
                    <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                  </div>
                  <Database className="absolute -bottom-6 -right-6 h-32 w-32 text-white opacity-10 transition-transform duration-500 group-hover:scale-110 group-hover:opacity-20" aria-hidden="true" />
                </Link>"""

desktop_new = """                <Link
                  href="/datasets"
                  className="relative overflow-hidden group mx-auto flex min-h-[220px] w-full max-w-[320px] flex-col justify-between rounded-2xl bg-primary/5 border border-primary/20 p-6 shadow-sm transition-all hover:-translate-y-1 hover:shadow-md hover:bg-primary/10"
                >
                  <div className="relative z-10">
                    <div className="flex items-center gap-2 mb-2">
                        <Sparkles className="h-4 w-4 text-primary" />
                        <p className="text-xs font-medium tracking-widest text-primary">发现更多</p>
                    </div>
                    <h3 className="mt-2 text-2xl font-bold tracking-tight text-foreground">全部数据集</h3>
                    <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
                      浏览完整数据集列表，细致筛选与检索，精准定位各类化学反应数据源。
                    </p>
                  </div>
                  <div className="relative z-10 mt-6 inline-flex w-fit items-center gap-2 rounded-full bg-primary/10 px-4 py-2 text-sm font-semibold text-primary transition-colors group-hover:bg-primary/20">
                    前往广场探索
                    <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                  </div>
                </Link>"""

content = content.replace(mobile_old, mobile_new)
content = content.replace(desktop_old, desktop_new)

with open('/home/zy/zhangyi/rxncommons/frontend/src/app/page.tsx', 'w') as f:
    f.write(content)

