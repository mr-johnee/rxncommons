import re

file_path = '/home/zy/zhangyi/rxncommons/frontend/src/app/admin/page.tsx'
with open(file_path, 'r') as f:
    content = f.read()

# Fix 1: Make selected status filter button visibly strictly distinct
old_button = """                <button
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

new_button = """                <button
                  key={s.value}
                  onClick={() => setFilterStatus(s.value as DatasetStatus | 'all')}
                  className={`flex flex-col items-center justify-center p-3 rounded-xl border transition-all relative ${
                    filterStatus === s.value
                      ? 'border-primary bg-primary text-white shadow-md scale-[1.02]'
                      : 'border-slate-200 bg-white text-slate-600 hover:border-primary/40 hover:bg-primary/5'
                  }`}
                >"""

content = content.replace(old_button, new_button)

# Also fix the subtitle/label color inside the button so it isn't gray when selected
old_label = """                    <span className="text-xs text-slate-500 mt-1">{s.count} 个</span>"""
new_label = """                    <span className={`text-xs mt-1 ${filterStatus === s.value ? 'text-primary-foreground/80' : 'text-slate-500'}`}>{s.count} 个</span>"""
content = content.replace(old_label, new_label)

# Fix the internal icon and label styles, they might be inheriting text colors
# We don't need to do much if there's no explicitly conflicting classes

# Fix 2: Hide "设为精选" if it's protected
old_feature_btn = """                  {req.status === 'approved' && (
                    <button
                      onClick={() => toggleFeatured(req.dataset_id, !isFeatured)}"""

new_feature_btn = """                  {req.status === 'approved' && isPublicVisible && (
                    <button
                      onClick={() => toggleFeatured(req.dataset_id, !isFeatured)}"""

content = content.replace(old_feature_btn, new_feature_btn)

with open(file_path, 'w') as f:
    f.write(content)

