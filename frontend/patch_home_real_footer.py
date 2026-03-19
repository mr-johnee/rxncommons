import re

file_path = "/home/zy/zhangyi/rxncommons/frontend/src/app/page.tsx"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace the start of Section 3
old_sec3_start = r"""      <section data-home-section="true" data-section-index="2" onClick={handleSectionClick} className="snap-start snap-always min-h-full bg-slate-50 px-6 py-10 lg:px-8">
        <div className="mx-auto flex min-h-full max-w-7xl flex-col justify-start pt-[8vh] md:pt-[10vh]">"""

new_sec3_start = """      <section data-home-section="true" data-section-index="2" onClick={handleSectionClick} className="snap-start snap-always min-h-full bg-slate-50 flex flex-col">
        <div className="mx-auto flex flex-1 w-full max-w-7xl flex-col justify-start pt-[8vh] md:pt-[10vh] px-6 lg:px-8">"""

if old_sec3_start in content:
    content = content.replace(old_sec3_start, new_sec3_start)
else:
    print("WARNING: SEC 3 START NOT FOUND")

# Replace the inner footer
old_inner_footer = r"""        {/* 内置Footer以便在全屏单页体验中仍能看到版权 */}
        <div className="mt-auto w-full pb-6 pt-10 text-center text-xs leading-5 text-slate-500">
          &copy; {new Date().getFullYear()} RxnCommons Chemistry Data Hub. All rights reserved.
        </div>
      </section>"""

new_inner_footer = """        {/* 单独留出的深色底部模块 */}
        <div className="mt-auto w-full bg-slate-900 border-t border-slate-800 px-6 py-8 sm:py-10 text-center">
          <div className="mx-auto max-w-4xl flex flex-col items-center gap-2 sm:gap-1.5 text-sm sm:text-base text-slate-400">
            <p className="font-medium text-slate-300">
              Lab of Jianzhuo Luo @ Tsinghua University
            </p>
            <p>
              Mengminwei Science and Technology Building, Tsinghua University, Beijing, China
            </p>
            <div className="mt-3 h-px w-16 bg-slate-700/50"></div>
            <p className="mt-3 text-xs sm:text-sm text-slate-500">
              &copy; {new Date().getFullYear()} RxnCommons Chemistry Data Hub. All rights reserved.
            </p>
          </div>
        </div>
      </section>"""

if old_inner_footer in content:
    content = content.replace(old_inner_footer, new_inner_footer)
else:
    print("WARNING: INNER FOOTER NOT FOUND")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("PATCH RUN COMPLETED.")
