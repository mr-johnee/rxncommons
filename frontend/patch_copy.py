import re

file_path = "/home/zy/zhangyi/rxncommons/frontend/src/app/datasets/[id]/page.tsx"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Change state definition
content = content.replace(
    'const [copied, setCopied] = useState(false);',
    'const [copiedAction, setCopiedAction] = useState<string | null>(null);'
)

# Replace handleCopyShare signature
content = content.replace(
    'const handleCopyShare = async (generateNew = false) => {',
    "const handleCopyShare = async (actionType: 'top_copy' | 'generate' | 'bottom_copy' = 'top_copy') => {\n    const generateNew = actionType === 'generate';"
)

# Fix handleCopyShare content near the end
content = content.replace(
    """      if (!copiedOk) {
        throw new Error("Copy command failed");
      }

      setCopied(true);
      setTimeout(() => setCopied(false), 2000);""",
    """      if (!copiedOk) {
        throw new Error("Copy command failed");
      }

      setCopiedAction(actionType);
      setTimeout(() => setCopiedAction(null), 2000);"""
)

# Update buttons
old_top_button = """                  {!dataset.is_password_protected && (
                    <button
                      onClick={() => handleCopyShare(false)}
                      className="px-4 py-3 min-h-[46px] border border-gray-200 border-l-0 rounded-r-lg bg-white hover:bg-gray-50 text-gray-700 font-medium text-sm transition-colors flex items-center shrink-0"
                      title="复制上方链接"
                    >
                      {copied ? <Check className="h-4 w-4 text-green-600" /> : <Copy className="h-4 w-4" />}
                    </button>
                  )}"""

new_top_button = """                  {!dataset.is_password_protected && (
                    <button
                      onClick={() => handleCopyShare('top_copy')}
                      className="px-4 py-3 min-h-[46px] border border-gray-200 border-l-0 rounded-r-lg bg-white hover:bg-gray-50 text-gray-700 font-medium text-sm transition-colors flex items-center shrink-0"
                      title="复制上方链接"
                    >
                      {copiedAction === 'top_copy' ? <Check className="h-4 w-4 text-green-600" /> : <Copy className="h-4 w-4" />}
                    </button>
                  )}"""

content = content.replace(old_top_button, new_top_button)


old_bottom_buttons = """                        <div className="flex flex-col sm:flex-row gap-3">
                          <button 
                            onClick={() => handleCopyShare(true)}
                            className="flex-1 px-4 py-2.5 text-sm font-medium bg-amber-600 text-white hover:bg-amber-700 active:bg-amber-800 rounded-lg transition-all flex items-center justify-center gap-2 shadow-md"
                          >
                            <RefreshCw className="h-4 w-4" />
                            生成新口令
                          </button>
                          <button 
                            onClick={() => handleCopyShare(false)}
                            className="flex-1 px-4 py-2.5 text-sm font-medium bg-amber-600/10 text-amber-800 border border-amber-600/20 hover:bg-amber-600/20 rounded-lg transition-all flex items-center justify-center gap-2"
                          >
                            <Copy className="h-4 w-4" />
                            复制专属链接
                          </button>
                        </div>"""

new_bottom_buttons = """                        <div className="flex flex-col sm:flex-row gap-3">
                          <button 
                            onClick={() => handleCopyShare('generate')}
                            className="flex-1 px-4 py-2.5 text-sm font-medium bg-amber-600 text-white hover:bg-amber-700 active:bg-amber-800 rounded-lg transition-all flex items-center justify-center gap-2 shadow-md"
                          >
                            {copiedAction === 'generate' ? <Check className="h-4 w-4" /> : <RefreshCw className="h-4 w-4" />}
                            {copiedAction === 'generate' ? '已生成并复制！' : '生成新口令'}
                          </button>
                          <button 
                            onClick={() => handleCopyShare('bottom_copy')}
                            className="flex-1 px-4 py-2.5 text-sm font-medium bg-amber-600/10 text-amber-800 border border-amber-600/20 hover:bg-amber-600/20 rounded-lg transition-all flex items-center justify-center gap-2"
                          >
                            {copiedAction === 'bottom_copy' ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                            {copiedAction === 'bottom_copy' ? '链接已复制！' : '复制专属链接'}
                          </button>
                        </div>"""

content = content.replace(old_bottom_buttons, new_bottom_buttons)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("PATCH APPLIED!")
