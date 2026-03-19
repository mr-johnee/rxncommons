import re
with open('/home/zy/zhangyi/rxncommons/backend/app/api/v1/endpoints/files.py', 'r') as f:
    content = f.read()

import_lines = "from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks\nfrom app.core.tasks import process_file_metadata\n"
content = re.sub(r'from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File,\s+Form', import_lines, content.replace('Form                                                                           from', 'Form\nfrom'))

func_sig = """def upload_file(
    dataset_id: UUID,
    version_num: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):"""
new_func_sig = """def upload_file(
    dataset_id: UUID,
    version_num: int = Form(...),
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):"""
content = content.replace(func_sig, new_func_sig)

after_commit = """
        db.commit()
        db.refresh(new_file)
        
        # Trigger background processing
        background_tasks.add_task(process_file_metadata, new_file.id)
"""
content = re.sub(r'\s+db\.commit\(\)\n\s+db\.refresh\(new_file\)', after_commit, content)

with open('/home/zy/zhangyi/rxncommons/backend/app/api/v1/endpoints/files.py', 'w') as f:
    f.write(content)
