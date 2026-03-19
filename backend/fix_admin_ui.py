import re

file_path = '/home/zy/zhangyi/rxncommons/frontend/src/app/admin/page.tsx'
with open(file_path, 'r') as f:
    content = f.read()

# Fix 1: Make selected chips highly pronounced with solid colors, like primary.
old_meta = """const STATUS_META: Record<string, { label: string; badge: string; chip: string; icon: any }> = {
  pending: {
    label: '待审核',
    badge: 'bg-amber-100 text-amber-800 border-amber-200',
    chip: 'bg-amber-50 text-amber-700 border-amber-200',
    icon: Clock3,
  },
  approved: {
    label: '已通过',
    badge: 'bg-emerald-100 text-emerald-800 border-emerald-200',
    chip: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    icon: CheckCircle2,
  },
  rejected: {
    label: '已拒绝',
    badge: 'bg-red-100 text-red-800 border-red-200',
    chip: 'bg-red-50 text-red-700 border-red-200',
    icon: XCircle,
  },
  revision_required: {
    label: '建议修改',
    badge: 'bg-orange-100 text-orange-800 border-orange-200',
    chip: 'bg-orange-50 text-orange-700 border-orange-200',
    icon: AlertTriangle,
  },
  canceled_by_user: {
    label: '用户取消',
    badge: 'bg-slate-100 text-slate-700 border-slate-200',
    chip: 'bg-slate-100 text-slate-700 border-slate-200',
    icon: Ban,
  },
};"""

new_meta = """const STATUS_META: Record<string, { label: string; badge: string; chip: string; selected_chip: string; icon: any }> = {
  pending: {
    label: '待审核',
    badge: 'bg-amber-100 text-amber-800 border-amber-200',
    chip: 'bg-amber-50 text-amber-700 border-amber-200',
    selected_chip: 'bg-amber-500 text-white border-amber-600',
    icon: Clock3,
  },
  approved: {
    label: '已通过',
    badge: 'bg-emerald-100 text-emerald-800 border-emerald-200',
    chip: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    selected_chip: 'bg-emerald-600 text-white border-emerald-700',
    icon: CheckCircle2,
  },
  rejected: {
    label: '已拒绝',
    badge: 'bg-red-100 text-red-800 border-red-200',
    chip: 'bg-red-50 text-red-700 border-red-200',
    selected_chip: 'bg-red-500 text-white border-red-600',
    icon: XCircle,
  },
  revision_required: {
    label: '建议修改',
    badge: 'bg-orange-100 text-orange-800 border-orange-200',
    chip: 'bg-orange-50 text-orange-700 border-orange-200',
    selected_chip: 'bg-orange-500 text-white border-orange-600',
    icon: AlertTriangle,
  },
  canceled_by_user: {
    label: '用户取消',
    badge: 'bg-slate-100 text-slate-700 border-slate-200',
    chip: 'bg-slate-100 text-slate-700 border-slate-200',
    selected_chip: 'bg-slate-600 text-white border-slate-700',
    icon: Ban,
  },
};"""

if old_meta in content:
    content = content.replace(old_meta, new_meta)
    print("META replaced successfully")

old_btn_clz = """                className={`px-3 py-1.5 text-xs rounded-full border transition-colors inline-flex items-center gap-1.5 ${
                  active
                    ? (meta ? `${meta.chip} shadow-sm` : 'bg-primary text-primary-foreground border-primary shadow-sm')
                    : 'bg-background text-muted-foreground border-input hover:bg-accent hover:text-accent-foreground'
                }`}"""

new_btn_clz = """                className={`px-3 py-1.5 text-xs rounded-full border transition-colors inline-flex items-center gap-1.5 ${
                  active
                    ? (meta ? `${meta.selected_chip} shadow-sm` : 'bg-primary text-primary-foreground border-primary shadow-sm')
                    : 'bg-background text-muted-foreground border-input hover:bg-slate-100 hover:text-slate-800'
                }`}"""

if old_btn_clz in content:
    content = content.replace(old_btn_clz, new_btn_clz)
    print("Button CLZ replaced successfully")

old_count_span = """<span className="rounded-full bg-white/70 px-1.5 py-0.5 text-[10px]">{count}</span>"""
new_count_span = """<span className={`rounded-full px-1.5 py-0.5 text-[10px] ${active ? 'bg-white/30 text-white' : 'bg-slate-100 text-slate-500'}`}>{count}</span>"""

if old_count_span in content:
    content = content.replace(old_count_span, new_count_span)
    print("Count Span replaced successfully")

old_feature_btn = """                  {req.status === 'approved' && (
                    <button
                      onClick={() => toggleFeatured(req.dataset_id, !isFeatured)}"""

new_feature_btn = """                  {req.status === 'approved' && isPublicVisible && (
                    <button
                      onClick={() => toggleFeatured(req.dataset_id, !isFeatured)}"""

if old_feature_btn in content:
    content = content.replace(old_feature_btn, new_feature_btn)
    print("Feature Btn replaced successfully")

with open(file_path, 'w') as f:
    f.write(content)

