import re

with open('/home/zy/zhangyi/rxncommons/frontend/src/app/page.tsx', 'r') as f:
    content = f.read()

mobile_feature_old = """          <div className="md:hidden mt-8 -mx-1 flex snap-x snap-mandatory gap-3 overflow-x-auto px-1 pb-1">
            <article className="min-w-[220px] snap-start rounded-2xl border border-slate-200 bg-white p-4 shadow-sm text-center">
              <div className="flex items-center justify-center gap-2 mb-3">
                <div className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 shrink-0">
                  <Database className="h-4 w-4 text-primary" />
                </div>
                <h3 className="text-base font-semibold text-foreground m-0">集中化的一站式数据查阅</h3>
              </div>
              <p className="text-sm leading-6 text-muted-foreground">打破文献附录与本地硬盘的数据孤岛，将零散的化学反应数据集中沉淀，面向研究者提供便捷的一站式查阅、检索与下载体验。</p>
            </article>
            <article className="min-w-[220px] snap-start rounded-2xl border border-slate-200 bg-white p-4 shadow-sm text-center">
              <div className="flex items-center justify-center gap-2 mb-3">
                <div className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 shrink-0">
                  <FlaskConical className="h-4 w-4 text-primary" />
                </div>
                <h3 className="text-base font-semibold text-foreground m-0">高标准的化学数据规范化</h3>
              </div>
              <p className="text-sm leading-6 text-muted-foreground">告别因背景信息缺失而导致的复用难题。平台强力支持对数据集的元数据及其各字段含义进行详尽的刻画与说明，让每一条数据语境都清晰可溯，极大降低后续使用的门槛。</p>
            </article>
            <article className="min-w-[220px] snap-start rounded-2xl border border-slate-200 bg-white p-4 shadow-sm text-center">
              <div className="flex items-center justify-center gap-2 mb-3">
                <div className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 shrink-0">
                  <Users className="h-4 w-4 text-primary" />
                </div>
                <h3 className="text-base font-semibold text-foreground m-0">精细化的权限与版本管理</h3>
              </div>
              <p className="text-sm leading-6 text-muted-foreground">提供灵活的「公开/私密」状态切换实现数据受控共享；同时内置严格的迭代溯源机制，完整追踪每一次数据集修订，全方位保护核心科研资产。</p>
            </article>
          </div>"""

mobile_feature_new = """          <div className="md:hidden mt-8 -mx-1 flex snap-x snap-mandatory gap-4 overflow-x-auto px-1 pb-4">
            <article className="min-w-[260px] snap-start rounded-3xl border border-slate-100 bg-white p-6 shadow-sm">
              <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/5 text-primary">
                <Database className="h-5 w-5" />
              </div>
              <h3 className="mb-3 text-lg font-bold tracking-tight text-foreground">集中化数据汇聚</h3>
              <p className="text-sm leading-relaxed text-muted-foreground/90">
                打破文献附录与本地硬盘的数据孤岛，将零散的化学反应数据沉淀于协作平台，提供高效的检索与下载通道。
              </p>
            </article>
            <article className="min-w-[260px] snap-start rounded-3xl border border-slate-100 bg-white p-6 shadow-sm">
              <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/5 text-primary">
                <FlaskConical className="h-5 w-5" />
              </div>
              <h3 className="mb-3 text-lg font-bold tracking-tight text-foreground">高标准数据规范</h3>
              <p className="text-sm leading-relaxed text-muted-foreground/90">
                透明化的全维度特征展示与元数据刻画，极大降低背景缺失带来的不确定性，成倍提升后续复用效率。
              </p>
            </article>
            <article className="min-w-[260px] snap-start rounded-3xl border border-slate-100 bg-white p-6 shadow-sm">
              <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/5 text-primary">
                <Users className="h-5 w-5" />
              </div>
              <h3 className="mb-3 text-lg font-bold tracking-tight text-foreground">全方位资产托管</h3>
              <p className="text-sm leading-relaxed text-muted-foreground/90">
                提供灵活的受控共享方案与严谨的版本溯源树。每一次修订均被完整追踪，实现权限粒度精细控制。
              </p>
            </article>
          </div>"""

content = content.replace(mobile_feature_old, mobile_feature_new)

with open('/home/zy/zhangyi/rxncommons/frontend/src/app/page.tsx', 'w') as f:
    f.write(content)

