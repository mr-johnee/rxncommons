import re
with open('/home/zy/zhangyi/rxncommons/backend/app/api/v1/endpoints/files.py', 'r') as f:
    content = f.read()

import_lines = """
import magic
from app.crud import crud_file, crud_dataset
"""
content = re.sub(r'from app.crud import crud_file, crud_dataset', import_lines, content)

validation_logic = """
    # Verify version exists
    version = crud_file.get_version_by_num(db, dataset_id, version_num)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    # Extension whitelist
    allowed_exts = [".csv", ".txt", ".xlsx", ".json", ".xml"]
    filename_lower = file.filename.lower()
    if not any(filename_lower.endswith(ext) for ext in allowed_exts):
        raise HTTPException(status_code=400, detail="File extension not allowed")

    # Magic Mime check
    file.file.seek(0)
    head_chunk = file.file.read(2048)
    mime_type = magic.from_buffer(head_chunk, mime=True)
    
    # We do a loose check for common text/excel mimes, or reject if it's executable
    if "executable" in mime_type or "x-sharedlib" in mime_type:
        raise HTTPException(status_code=400, detail="Executable files are forbidden")
"""
content = re.sub(r'    # Verify version exists\n.*?raise HTTPException\(status_code=404, detail="Version not found"\)', validation_logic, content, flags=re.DOTALL)

with open('/home/zy/zhangyi/rxncommons/backend/app/api/v1/endpoints/files.py', 'w') as f:
    f.write(content)
