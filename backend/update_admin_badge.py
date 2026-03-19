import re

with open("../frontend/src/app/admin/page.tsx", "r", encoding="utf-8") as f:
    content = f.read()

# We need to find the badge section and replace it.
# The section starts with {isProtected ? ( and ends right before </div>\n                </div>\n\n                <div className="flex flex-wrap items-center gap-2">

badge_code = """                    {(() => {
                      if (isProtected) {
                        return (
                          <span className="inline-flex items-center gap-1 rounded-full border border-amber-200 bg-amber-50 px-2 py-1 text-amber-700">
                            <LockKeyhole className="h-3 w-3" />
                            隐私数据集
                          </span>
                        );
                      }
                      
                      if (req.status === 'approved') {
                        return isPublicVisible ? (
                          <span className="inline-flex items-center gap-1 rounded-full border border-sky-200 bg-sky-50 px-2 py-1 text-sky-700">
                            <Eye className="h-3 w-3" />
                            已发布可见
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 rounded-full border border-slate-200 bg-slate-100 px-2 py-1 text-slate-700">
                            <EyeOff className="h-3 w-3" />
                            数据集全局不可见
                          </span>
                        );
                      }
                      
                      if (req.status === 'pending') {
                        return req.dataset?.dataset_status === 'published' ? (
                          <span className="inline-flex items-center gap-1 rounded-full border border-amber-200 bg-amber-50 px-2 py-1 text-amber-700">
                            <Clock className="h-3 w-3" />
                            新版本审核中(暂不可见)
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 rounded-full border border-slate-200 bg-slate-100 px-2 py-1 text-slate-700">
                            <EyeOff className="h-3 w-3" />
                            普通用户不可见
                          </span>
                        );
                      }
                      
                      // rejected 等
                      return (
                        <span className="inline-flex items-center gap-1 rounded-full border border-slate-200 bg-slate-100 px-2 py-1 text-slate-700">
                          <EyeOff className="h-3 w-3" />
                          该版本不可见
                        </span>
                      );
                    })()}"""

# We search for the old badge block
pattern = re.compile(r"\{\s*isProtected \? \(\s*<span.*?隐私数据集\s*</span>\s*\)\s*:\s*isPublicVisible \? \(\s*<span.*?普通用户可见\s*</span>\s*\)\s*:\s*\(\s*<span.*?普通用户不可见\s*</span>\s*\)\s*\}", re.DOTALL)

if pattern.search(content):
    new_content = pattern.sub(badge_code, content)
    with open("../frontend/src/app/admin/page.tsx", "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Success")
else:
    print("Regex failed to match!")
