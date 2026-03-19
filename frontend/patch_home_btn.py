import re

file_path = "/home/zy/zhangyi/rxncommons/frontend/src/app/page.tsx"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Make sure Upload is imported
if "import { Search, ArrowRight, Database, FlaskConical, Users, Sparkles, ThumbsUp, ArrowDownToLine, ChevronsDown } from 'lucide-react';" in content:
    content = content.replace(
        "import { Search, ArrowRight, Database, FlaskConical, Users, Sparkles, ThumbsUp, ArrowDownToLine, ChevronsDown } from 'lucide-react';", 
        "import { Search, ArrowRight, Database, FlaskConical, Users, Sparkles, ThumbsUp, ArrowDownToLine, ChevronsDown, Upload } from 'lucide-react';"
    )

old_upload = """            ) : (
              <Link href="/upload" className="group flex w-full items-center justify-center gap-2 rounded-full border border-slate-200 bg-white px-8 py-3 text-sm font-medium text-slate-700 shadow-sm transition-all hover:bg-slate-50 hover:text-primary sm:w-auto hover:-translate-y-0.5">
                上传数据集 <span aria-hidden="true" className="transition-transform group-hover:translate-x-1">→</span>
              </Link>
            )}"""

new_upload = """            ) : (
              <Link href="/upload" className="group flex w-full items-center justify-center gap-2 rounded-full border border-teal-200 bg-teal-50/50 px-8 py-3 text-sm font-medium text-teal-700 shadow-sm transition-all hover:bg-teal-100 hover:text-teal-800 hover:border-teal-300 sm:w-auto hover:-translate-y-0.5">
                <Upload className="h-4 w-4" /> 上传数据集 <span aria-hidden="true" className="transition-transform group-hover:translate-x-1">→</span>
              </Link>
            )}"""

if old_upload in content:
    content = content.replace(old_upload, new_upload)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("HOME PAGE PATCH APPLIED!")
else:
    print("HOME PAGE UPLOAD BTN NOT LOCATED!")
