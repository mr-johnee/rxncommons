import re

file_path = "/home/zy/zhangyi/rxncommons/frontend/src/app/datasets/[id]/page.tsx"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

old_block = """            <div className="p-6 space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {dataset.is_password_protected ? '基础链接 (需对方手动输入口令)' : '公开直达链接'}
                </label>
                <div className="flex items-center">
                  <div className="bg-gray-50 flex-1 p-3 rounded-l-lg text-sm text-gray-600 break-all border border-gray-200 border-r-0 select-all font-mono">
                    {typeof window !== 'undefined' ? window.location.origin : ''}/datasets/{encodeURIComponent(dataset.owner?.username || '')}/{dataset.slug}
                  </div>
                  <button
                    onClick={() => handleCopyShare(false)}
                    className="px-4 py-3 min-h-[46px] border border-gray-200 border-l-0 rounded-r-lg bg-white hover:bg-gray-50 text-gray-700 font-medium text-sm transition-colors flex items-center"
                    title="复制上方链接"
                  >
                    {copied ? <Check className="h-4 w-4 text-green-600" /> : <Copy className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              {dataset.is_password_protected && (
                <div className="relative overflow-hidden rounded-xl border border-amber-200 bg-gradient-to-br from-amber-50 to-orange-50/30">
                  <div className="p-5">
                    <div className="flex items-start gap-3">
                      <div className="p-1.5 bg-amber-100 rounded-md text-amber-700 mt-0.5 shadow-sm">
                        <KeyRound className="h-4 w-4" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-3">
                          <h4 className="text-[15px] font-semibold text-amber-900">私密数据集专属邀请</h4>
                          {(dataset.access_password || sharePassword.trim()) && (
                            <div className="px-2.5 py-1 bg-white border border-amber-200 rounded text-xs font-mono text-amber-700 shadow-sm">
                              当前口令: {sharePassword.trim() || dataset.access_password}
                            </div>
                          )}
                        </div>
                        <p className="text-[13px] leading-relaxed text-amber-800/80 mb-4">
                          只要带有免密口令的专属链接，任何人点击均可直接跳过密码验证访问。你可以复制下方生成的免密专属链接发给对方，或者随时点击重新生成来使旧口令失效。
                        </p>
                        <div className="flex flex-col sm:flex-row gap-3">
                          <button 
                            onClick={() => handleCopyShare(false)}
                            className="flex-1 px-4 py-2.5 text-sm font-medium bg-amber-600/10 text-amber-800 border border-amber-600/20 hover:bg-amber-600/20 rounded-lg transition-all flex items-center justify-center gap-2"
                          >
                            <Copy className="h-4 w-4" />
                            复制免密专属链接
                          </button>
                          <button 
                            onClick={() => handleCopyShare(true)}
                            className="flex-1 px-4 py-2.5 text-sm font-medium bg-amber-600 text-white hover:bg-amber-700 active:bg-amber-800 rounded-lg transition-all flex items-center justify-center gap-2 shadow-md"
                          >
                            <RefreshCw className="h-4 w-4" />
                            生成新口令并复制
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>"""

new_block = """            <div className="p-6 space-y-6 overflow-hidden">
              <div>
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
              </div>

              {dataset.is_password_protected && (
                <div className="relative overflow-hidden rounded-xl border border-amber-200 bg-gradient-to-br from-amber-50 to-orange-50/30">
                  <div className="p-5">
                    <div className="flex items-start gap-3">
                      <div className="p-1.5 bg-amber-100 rounded-md text-amber-700 mt-0.5 shadow-sm">
                        <KeyRound className="h-4 w-4" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-3 gap-2">
                          <h4 className="text-[15px] font-semibold text-amber-900 truncate">私密数据集专属邀请</h4>
                          {(dataset.access_password || sharePassword.trim()) && (
                            <div className="px-2.5 py-1 bg-white border border-amber-200 rounded text-xs font-mono text-amber-700 shadow-sm shrink-0">
                              当前口令: {sharePassword.trim() || dataset.access_password}
                            </div>
                          )}
                        </div>
                        <p className="text-[13px] leading-relaxed text-amber-800/80 mb-4">
                          通过专属链接，访客可免密直接访问此数据集。重新生成将使旧口令失效。
                        </p>
                        <div className="flex flex-col sm:flex-row gap-3">
                          <button 
                            onClick={() => handleCopyShare(true)}
                            className="flex-1 px-4 py-2.5 text-sm font-medium bg-amber-600 text-white hover:bg-amber-700 active:bg-amber-800 rounded-lg transition-all flex items-center justify-center gap-2 shadow-md"
                          >
                            <RefreshCw className="h-4 w-4" />
                            生成新口令并复制
                          </button>
                          <button 
                            onClick={() => handleCopyShare(false)}
                            className="flex-1 px-4 py-2.5 text-sm font-medium bg-amber-600/10 text-amber-800 border border-amber-600/20 hover:bg-amber-600/20 rounded-lg transition-all flex items-center justify-center gap-2"
                          >
                            <Copy className="h-4 w-4" />
                            复制免密专属链接
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>"""

if old_block in content:
    content = content.replace(old_block, new_block)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("PATCH APPLIED SUCCESSFULLY")
else:
    print("COULD NOT FIND BLOCK TO REPLACE")

