import re

file_path = "/home/zy/zhangyi/rxncommons/frontend/src/app/profile/page.tsx"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add Lock and Globe2 to imports
if "from 'lucide-react'" in content:
    content = re.sub(
        r"import \{([^}]+)\} from 'lucide-react';",
        lambda m: f"import {{{m.group(1).replace('Lock, ', '').replace('Globe2, ', '')}, Lock, Globe2}} from 'lucide-react';",
        content
    )

# 2. Add privacyFilter state and handleTogglePrivacy function right after setCopiedId
logic_injection = """  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [privacyFilter, setPrivacyFilter] = useState<'all' | 'public' | 'password_protected'>('all');

  const handleTogglePrivacy = async (ds: any) => {
    const isPrivate = ds.access_level === 'password_protected';
    const actionName = isPrivate ? '公开' : '私密';
    const confirmed = confirm(`确认将「${ds.title}」设为${actionName}吗？${isPrivate ? '公开后所有人均可访问和搜索该数据集。' : '私密后仅拥有专属链接的人可访问，且不对外检索。'}`);
    if (!confirmed) return;
    
    try {
      const payload: any = { access_level: isPrivate ? 'public' : 'password_protected' };
      if (!isPrivate) {
         payload.access_password = ds.access_password || Math.random().toString(36).slice(-8);
      }
      const res = await api.put(`/datasets/${ds.id}/access-policy`, payload);
      setDatasets((prev) => prev.map((item: any) => 
        item.id === ds.id ? { ...item, access_level: res.data?.access_level, access_password: payload.access_password || item.access_password } : item
      ));
    } catch (err: any) {
      alert(`操作失败：${err.response?.data?.detail || err.message}`);
    }
  };"""

content = re.sub(r'  const \[copiedId, setCopiedId\] = useState<string \| null>\(null\);', logic_injection, content, count=1)

# 3. Update the filtered logic
old_filter = "  const filtered = tab === 'all' ? datasets : datasets.filter(d => d.dataset_status === tab);"
new_filter = """  const filtered = datasets.filter(d => {
    if (tab !== 'all' && d.dataset_status !== tab) return false;
    if (privacyFilter !== 'all') {
      const isPriv = d.access_level === 'password_protected';
      if (privacyFilter === 'password_protected' && !isPriv) return false;
      if (privacyFilter === 'public' && isPriv) return false;
    }
    return true;
  });"""
content = content.replace(old_filter, new_filter)

# 4. Update Header Tabs to include privacy select
old_tabs_html_pattern = re.compile(r'      \{\/\* Tabs \+ create button \*\/\}.*?      <div className="bg-white', re.DOTALL)
match = old_tabs_html_pattern.search(content)

if match:
    old_tabs = match.group(0)
    new_tabs = r"""      {/* Tabs + create button */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex gap-1">
            {(<span className="hidden"></span>) || ([['all', '全部'], ['draft', '草稿'], ['pending_review', '审核中'], ['published', '已发布'], ['revision_required', '需修改']] as const).map(([key, label]) => (
              <button key={key} onClick={() => setTab(key)}
                className={`px-3 py-1.5 rounded-md text-sm font-medium border transition-colors ${tab === key ? 'bg-primary text-primary-foreground border-primary shadow-sm' : 'bg-background text-muted-foreground border-input hover:bg-accent hover:text-accent-foreground'}`}>
                {label} {key === 'all' ? `(${datasets.length})` : counts[key] ? `(${counts[key]})` : ''}
              </button>
            ))}
          </div>
          <div className="h-5 w-px bg-border hidden sm:block mx-1"></div>
          <select 
            className="text-sm bg-background border border-input rounded-md px-2 py-1.5 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/20 text-foreground cursor-pointer"
            value={privacyFilter}
            onChange={(e) => setPrivacyFilter(e.target.value as any)}
          >
            <option value="all">所有可见度</option>
            <option value="public">🌐 公开</option>
            <option value="password_protected">🔒 私密</option>
          </select>
        </div>
        
        {user.role === 'admin' ? (
          <Link href="/admin" className="bg-primary text-primary-foreground shadow hover:bg-primary/90 px-4 py-2 rounded-md text-sm font-medium transition-colors whitespace-nowrap text-center">
            进入管理后台
          </Link>
        ) : (
          <Link href="/upload" className="bg-primary text-primary-foreground shadow hover:bg-primary/90 px-4 py-2 rounded-md text-sm font-medium transition-colors whitespace-nowrap text-center">
            创建新数据集
          </Link>
        )}
      </div>

      <div className="bg-white"""
    content = content[:match.start()] + new_tabs + content[match.end():]
else:
    print("WARNING: Tabs Pattern Not Found")

# 5. Inject Privacy button next to the Status badge
old_badge = r"""                    <span className={`px-2 py-1 rounded text-xs font-semibold ${STATUS_STYLE[ds.dataset_status] || 'bg-gray-100 text-gray-700'}`}>
                      {STATUS_LABEL[ds.dataset_status] || ds.dataset_status}
                    </span>"""

new_badge = """                    <span className={`px-2 py-1 rounded text-xs font-semibold ${STATUS_STYLE[ds.dataset_status] || 'bg-gray-100 text-gray-700'}`}>
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
                    )}"""

content = content.replace(old_badge, new_badge)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("PROFILE PAGE PATCH APPLIED!")
