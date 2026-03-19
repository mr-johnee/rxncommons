with open("../frontend/src/app/admin/page.tsx", "r", encoding="utf-8") as f:
    text = f.read()

start_str = "                    {isProtected ? ("
end_str = "                    )}\n                  </div>"

if start_str in text and end_str in text:
    start_idx = text.find(start_str)
    end_idx = text.find(end_str) + len(end_str) - 26 # exclude </div>
    
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
                            该版本已发布可见
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
    
    new_text = text[:start_idx] + badge_code + text[end_idx:]
    with open("../frontend/src/app/admin/page.tsx", "w", encoding="utf-8") as f:
        f.write(new_text)
    print("Success replacing!")
else:
    print("Start or end not found")
