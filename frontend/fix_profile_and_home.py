import re

file_profile = "/home/zy/zhangyi/rxncommons/frontend/src/app/profile/page.tsx"
with open(file_profile, "r", encoding="utf-8") as f:
    p_content = f.read()

# Fix duplicates in profile
# Find the `<td className="p-4">` that contains the status and badges.
# We'll use regex to rewrite that entire column neatly.
pattern_td = r'<td className="p-4">\s*<span className=\{`px-2 py-1.*?</td>'
match = re.search(pattern_td, p_content, flags=re.DOTALL)
if match:
    # replace the entire td content with a clean flex layout
    clean_td = """<td className="p-4">
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${STATUS_STYLE[ds.dataset_status] || 'bg-gray-100 text-gray-700'}`}>
                        {STATUS_LABEL[ds.dataset_status] || ds.dataset_status}
                      </span>
                      {ds.access_level === 'password_protected' ? (
                        <button onClick={(e) => { e.preventDefault(); handleTogglePrivacy(ds); }} title="目前为私密，点击可设为公开" className="flex items-center gap-1 px-2 py-1 rounded text-xs font-medium bg-amber-50 text-amber-600 border border-amber-200/50 hover:bg-amber-100 hover:text-amber-700 transition-colors">
                          <Lock className="w-3 h-3" />
                          私密
                        </button>
                      ) : (
                        <button onClick={(e) => { e.preventDefault(); handleTogglePrivacy(ds); }} title="目前为公开，点击可设为私密" className="flex items-center gap-1 px-2 py-1 rounded text-xs font-medium bg-emerald-50 text-emerald-600 border border-emerald-200/50 hover:bg-emerald-100 hover:text-emerald-700 transition-colors">
                          <Globe2 className="w-3 h-3" />
                          公开
                        </button>
                      )}
                    </div>
                  </td>"""
    p_content = p_content[:match.start()] + clean_td + p_content[match.end():]
    with open(file_profile, "w", encoding="utf-8") as f:
        f.write(p_content)
    print("PROFILE FIXED")


file_home = "/home/zy/zhangyi/rxncommons/frontend/src/app/page.tsx"
with open(file_home, "r", encoding="utf-8") as f:
    h_content = f.read()

# 1. Change "浏览全部数据集" to "浏览数据集" with an icon
# Old: 
#             <Link
#               href="/datasets"
#               className="w-full sm:w-auto text-center rounded-full bg-slate-100 px-8 py-3 text-sm font-medium text-slate-700 shadow-sm transition-all hover:bg-slate-200 hover:shadow hover:-translate-y-0.5"
#             >
#               浏览全部数据集
#             </Link>
h_old_browse = r"""<Link
              href="/datasets"
              className="w-full sm:w-auto text-center rounded-full bg-slate-100 px-8 py-3 text-sm font-medium text-slate-700 shadow-sm transition-all hover:bg-slate-200 hover:shadow hover:-translate-y-0.5"
            >
              浏览全部数据集
            </Link>"""
h_new_browse = """<Link
              href="/datasets"
              className="group flex w-full items-center justify-center gap-2 rounded-full bg-slate-100 px-8 py-3 text-sm font-medium text-slate-700 shadow-sm transition-all hover:bg-slate-200 hover:shadow hover:-translate-y-0.5 sm:w-auto"
            >
              <Database className="h-4 w-4 text-slate-500 group-hover:text-slate-700 transition-colors" />
              浏览数据集
            </Link>"""
if h_old_browse in h_content:
    h_content = h_content.replace(h_old_browse, h_new_browse)
else:
    print("BROWSE LINK NOT FOUND")

# 2. Remove Arrow from Upload Dataset & Admin Panel
# Let's clean up both 'admin' and 'upload' buttons
h_old_admin = r"""<Link href="/admin" className="group flex w-full items-center justify-center gap-2 rounded-full border border-slate-200 bg-white px-8 py-3 text-sm font-medium text-slate-700 shadow-sm transition-all hover:bg-slate-50 hover:text-primary sm:w-auto hover:-translate-y-0.5">
                进入管理后台 <span aria-hidden="true" className="transition-transform group-hover:translate-x-1">→</span>
              </Link>"""
h_new_admin = """<Link href="/admin" className="flex w-full items-center justify-center gap-2 rounded-full border border-slate-200 bg-white px-8 py-3 text-sm font-medium text-slate-700 shadow-sm transition-all hover:bg-slate-50 hover:text-primary sm:w-auto hover:-translate-y-0.5">
                进入管理后台
              </Link>"""
h_content = h_content.replace(h_old_admin, h_new_admin)

h_old_upload = r"""<Link href="/upload" className="group flex w-full items-center justify-center gap-2 rounded-full border border-teal-200 bg-teal-50/50 px-8 py-3 text-sm font-medium text-teal-700 shadow-sm transition-all hover:bg-teal-100 hover:text-teal-800 hover:border-teal-300 sm:w-auto hover:-translate-y-0.5">
                <Upload className="h-4 w-4" /> 上传数据集 <span aria-hidden="true" className="transition-transform group-hover:translate-x-1">→</span>
              </Link>"""
h_new_upload = """<Link href="/upload" className="flex w-full items-center justify-center gap-2 rounded-full border border-teal-200 bg-teal-50/50 px-8 py-3 text-sm font-medium text-teal-700 shadow-sm transition-all hover:bg-teal-100 hover:text-teal-800 hover:border-teal-300 sm:w-auto hover:-translate-y-0.5">
                <Upload className="h-4 w-4" /> 上传数据集
              </Link>"""
h_content = h_content.replace(h_old_upload, h_new_upload)

with open(file_home, "w", encoding="utf-8") as f:
    f.write(h_content)
print("HOME FIXED")
