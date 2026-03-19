import re
with open('/home/zy/zhangyi/rxncommons/backend/app/api/v1/endpoints/versions.py', 'r') as f:
    content = f.read()

import_lines = "from app.core.storage import minio_client\nfrom datetime import timedelta\n"
content = import_lines + content

old_download = """def download_all_files(
    dataset_id: UUID,
    version_num: int,
    db: Session = Depends(deps.get_db)
):
    dataset = crud_dataset.get_dataset(db, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    # Increment download count
    dataset.download_count += 1
    db.commit()
    return {"status": "success", "url": "https://minio-url/archive/dataset.zip"}"""

new_download = """def download_all_files(
    dataset_id: UUID,
    version_num: int,
    db: Session = Depends(deps.get_db)
):
    dataset = crud_dataset.get_dataset(db, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    version = db.query(DatasetVersion).filter(DatasetVersion.dataset_id == dataset_id, DatasetVersion.version_num == version_num).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
        
    if not version.archive_key:
        raise HTTPException(status_code=400, detail="Archive not fully built yet, please try again later")

    # Increment download count
    dataset.download_count += 1
    db.commit()
    
    try:
        url = minio_client.presigned_get_object(
            "rxncommons-bucket",
            version.archive_key,
            expires=timedelta(hours=2)
        )
        return {"status": "success", "url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))"""

content = content.replace(old_download, new_download)

with open('/home/zy/zhangyi/rxncommons/backend/app/api/v1/endpoints/versions.py', 'w') as f:
    f.write(content)
