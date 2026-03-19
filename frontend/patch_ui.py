import re

file_path = "/home/zy/zhangyi/rxncommons/frontend/src/app/datasets/[id]/page.tsx"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

old_block = """              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {!dataset.is_password_protected 
                    ? '公开直达链接' 
                    : (dataset.access_password || sharePassword.trim()) 
                      ? '免密专属链接' 
                      : '基础链接 (需对方手动输入口令)'}
                </label>
                <div className="flex items-center max-w-full">
                  <div className="bg-gray-50 flex-1 p-3 rounded-l-lg text-sm text-gray-600 truncate overflow-x-auto scrollbar-hide border border-gray-200 border-r-0 select-all font-mono whitespace-nowrap min-w-0">
                    {typeof window !== 'undefined' ? window.location.origin : ''}/datasets/{encodeURIComponent(dataset.owner?.username || '')}/{dataset.slug}
                    {(dataset.is_password_protected && (dataset.access_password || sharePassword.trim())) 
                      ? `?share_token=${sharePassword.trim() || dataset.access_password}`
                      : ''}
                  </div>
                  <button
                    onClick={() => handleCopyShare(false)}
                    className="px-4 py-3 min-h-[46px] border border-gray-200 border-l-0 rounded-r-lg bg-white hover:bg-gray-50 text-gray-700 font-medium text-sm transition-colors flex items-center shrink-0"
                    title="复制上方链接"
                  >
                    {copied ? <Check className="h-4 w-4 text-green-600" /> : <Copy className="h-4 w-4" />}
                  </button>
                </div>
              </div>"""

new_block = """              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {!dataset.is_password_protected 
                    ? '公开直达链接' 
                    : (dataset.access_password || sharePassword.trim()) 
                      ? '免密专属链接' 
                      : '基础链接 (需对方手动输入口令)'}
                </label>
                <div className="flex items-stretch max-w-full">
                  <div className={`bg-gray-50 flex-1 p-3 text-sm text-gray-600 break-all border border-gray-200 select-all font-mono ${dataset.is_password_protected ? 'rounded-lg' : 'rounded-l-lg border-r-0'}`}>
                    {typeof window !== 'undefined' ? window.location.origin : ''}/datasets/{encodeURIComponent(dataset.owner?.username || '')}/{dataset.slug}
                    {(dataset.is_password_protected && (dataset.access_password || sharePassword.trim())) 
                      ? `?share_token=${sharePassword.trim() || dataset.access_password}`
                      : ''}
                  </div>
                  {!dataset.is_password_protected && (
                    <button
                      onClick={() => handleCopyShare(false)}
                      className="px-4 py-3 min-h-[46px] border border-gray-200 border-l-0 rounded-r-lg bg-white hover:bg-gray-50 text-gray-700 font-medium text-sm transition-colors flex items-center shrink-0"
                      title="复制上方链接"
                    >
                      {copied ? <Check className="h-4 w-4 text-green-600" /> : <Copy className="h-4 w-4" />}
                    </button>
                  )}
                </div>
              </div>"""

if old_block in content:
    content = content.replace(old_block, new_block)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("PATCH APPLIED!")
else:
    print("NOT FOUND!")
