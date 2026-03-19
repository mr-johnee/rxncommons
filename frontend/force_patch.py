import re

file_path = "/home/zy/zhangyi/rxncommons/frontend/src/app/datasets/[id]/page.tsx"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace the div containing the link
content = re.sub(
    r'<div className="bg-gray-50 flex-1 p-3[^>]+>',
    r'<div className={`bg-gray-50 flex-1 p-3 text-sm text-gray-600 break-all border border-gray-200 select-all font-mono ${dataset.is_password_protected ? \'rounded-lg\' : \'rounded-l-lg border-r-0\'}`}>',
    content
)

# Replace the copy button conditional
content = content.replace(
    '<button\n                    onClick={() => handleCopyShare(false)}',
    '{!dataset.is_password_protected && (\n                    <button\n                      onClick={() => handleCopyShare(false)}'
)

# And add the closing brace for the conditional if we just added it
content = content.replace(
    '</button>\n                </div>\n              </div>\n\n              {dataset.is_password_protected',
    '</button>\n                  )}\n                </div>\n              </div>\n\n              {dataset.is_password_protected'
)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("FORCE PATCH APPLIED")
