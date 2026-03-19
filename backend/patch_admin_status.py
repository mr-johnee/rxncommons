import re

with open('/home/zy/zhangyi/rxncommons/frontend/src/app/admin/page.tsx', 'r') as f:
    content = f.read()

old_status_ui = """                <button
                  key={s.value}
                  onClick={() => setFilterStatus(s.value as DatasetStatus | 'all')}
                  className={`flex flex-col items-center justify-center p-3 rounded-xl border transition-all ${
                    filterStatus === s.value
                      ? 'border-primary bg-primary/5 text-primary shadow-sm'
                      : 'border-slate-200 bg-white hover:border-primary/30 hover:bg-slate-50'
                  }`}
                >"""

new_status_ui = """                <button
                  key={s.value}
                  onClick={() => setFilterStatus(s.value as DatasetStatus | 'all')}
                  className={`flex flex-col items-center justify-center p-3 rounded-xl border transition-all relative ${
                    filterStatus === s.value
                      ? 'border-primary ring-1 ring-primary bg-primary/5 text-primary shadow-sm scale-[1.02]'
                      : 'border-slate-200 bg-white text-slate-600 hover:border-primary/40 hover:bg-primary/5'
                  }`}
                >
                  {filterStatus === s.value && (
                    <div className="absolute top-0 right-0 -mt-1 -mr-1 h-3 w-3 rounded-full bg-primary ring-2 ring-white"></div>
                  )}"""

content = content.replace(old_status_ui, new_status_ui)

with open('/home/zy/zhangyi/rxncommons/frontend/src/app/admin/page.tsx', 'w') as f:
    f.write(content)

