import re

file_path = "/home/zy/zhangyi/rxncommons/frontend/src/app/profile/page.tsx"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# We have duplicated blocks because of bad regex. We need to find the correct boundaries and fix it.
# The area is between <div className="mb-6"> and {/* Table */}
start_str = '      {/* Tabs + create button */}'
end_str = '      {/* Table */}'

start_idx = content.find(start_str)
end_idx = content.find(end_str)

if start_idx != -1 and end_idx != -1:
    old_section = content[start_idx:end_idx]
    
    new_section = r"""      {/* Tabs + create button */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex gap-1">
            {([['all', '全部'], ['draft', '草稿'], ['pending_review', '审核中'], ['published', '已发布'], ['revision_required', '需修改']] as const).map(([key, label]) => (
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

"""
    content = content[:start_idx] + new_section + content[end_idx:]
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("PATCH APPLIED CLEANLY")
else:
    print("COULD NOT FIND BOUNDARIES")
