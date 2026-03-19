import re

file_path = "/home/zy/zhangyi/rxncommons/frontend/src/components/Navbar.tsx"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Make sure Upload is imported
if "import { User, ChevronDown, LogOut, LayoutDashboard } from" in content:
    content = content.replace(
        "import { User, ChevronDown, LogOut, LayoutDashboard } from", 
        "import { User, ChevronDown, LogOut, LayoutDashboard, Upload } from"
    )

old_upload = """                {showUploadEntry && (
                  <Link
                    href="/upload"
                    className="hidden sm:inline-flex items-center justify-center rounded-full bg-primary px-4 py-1.5 text-sm font-semibold text-white shadow-md transition-all hover:bg-primary/90 hover:shadow-lg active:scale-95 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                  >
                    上传数据集
                  </Link>
                )}"""

new_upload = """                {showUploadEntry && (
                  <Link
                    href="/upload"
                    className="hidden sm:inline-flex items-center justify-center gap-1.5 rounded-full bg-gradient-to-r from-teal-600 to-primary px-5 py-1.5 text-sm font-semibold text-white shadow-md transition-all hover:from-teal-500 hover:to-primary/90 hover:shadow-lg hover:-translate-y-0.5 active:scale-95 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                  >
                    <Upload className="h-4 w-4" />
                    <span>上传数据</span>
                  </Link>
                )}"""

if old_upload in content:
    content = content.replace(old_upload, new_upload)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("NAVBAR PATCH APPLIED!")
else:
    print("NAVBAR UPLOAD BTN NOT LOCATED!")
