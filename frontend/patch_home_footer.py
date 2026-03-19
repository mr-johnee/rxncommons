import re

file_path = "/home/zy/zhangyi/rxncommons/frontend/src/app/page.tsx"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Inject body overflow hidden
overflow_style = """
  return (
    <div ref={scrollRef} className="h-[calc(100svh-3.5rem)] overflow-y-auto overscroll-y-contain snap-y snap-mandatory scroll-smooth relative">
      <style dangerouslySetInnerHTML={{ __html: `body { overflow: hidden !important; }` }} />
"""
content = re.sub(r'  return \(\n\s*<div ref=\{scrollRef\} className="h-\[calc\(100svh-3\.5rem\)\].*?">\n', overflow_style, content, flags=re.DOTALL)

# 2. Add inline footer to the end of section 3
end_of_section3 = """              </p>
            </article>
          </div>
        </div>
        
        {/* 内置Footer以便在全屏单页体验中仍能看到版权 */}
        <div className="mt-auto w-full pb-6 pt-10 text-center text-xs leading-5 text-slate-500">
          &copy; {new Date().getFullYear()} RxnCommons Chemistry Data Hub. All rights reserved.
        </div>
      </section>
    </div>
  );
}"""

content = re.sub(r'              </p>\n            </article>\n          </div>\n        </div>\n      </section>\n    </div>\n  \);\n}', end_of_section3, content, flags=re.DOTALL)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("PATCH APPLIED!")
