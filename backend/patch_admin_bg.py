import re
with open('/home/zy/zhangyi/rxncommons/backend/app/api/v1/endpoints/admin.py', 'r') as f:
    content = f.read()

import_lines = "from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks\nfrom app.core.tasks import pack_version_archive\n"
content = re.sub(r'from fastapi import APIRouter, Depends, HTTPException, status', import_lines, content)

func_sig = """def approve_review_request(
    request_id: UUID,
    db: Session = Depends(deps.get_db),
    admin: User = Depends(get_current_admin)
):"""
new_func_sig = """def approve_review_request(
    request_id: UUID,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(deps.get_db),
    admin: User = Depends(get_current_admin)
):"""
content = content.replace(func_sig, new_func_sig)

after_commit = """
    # Normally emit task to sync search_document and generate zip
    background_tasks.add_task(pack_version_archive, version.id)
"""
content = re.sub(r'\s+# Normally emit task to sync search_document and generate zip', after_commit, content)

with open('/home/zy/zhangyi/rxncommons/backend/app/api/v1/endpoints/admin.py', 'w') as f:
    f.write(content)
