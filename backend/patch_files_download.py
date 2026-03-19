import re
with open('/home/zy/zhangyi/rxncommons/backend/app/api/v1/endpoints/files.py', 'r') as f:
    content = f.read()

download_endpoint = """
from app.models.dataset import DatasetFile
from app.core.storage import minio_client
from datetime import timedelta

@router.get("/{file_id}/download")
def download_file(
    file_id: int,
    db: Session = Depends(deps.get_db)
):
    dataset_file = db.query(DatasetFile).filter(DatasetFile.id == file_id).first()
    if not dataset_file:
        raise HTTPException(status_code=404, detail="File not found")
        
    # Generate presigned url from minio
    try:
        url = minio_client.get_presigned_url(
            "GET",
            "rxncommons-bucket",
            f"objects/{dataset_file.file_key}",
            expires=timedelta(hours=1)
        )
        return {"status": "success", "url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not generate download url: {e}")
"""

content += "\n" + download_endpoint

with open('/home/zy/zhangyi/rxncommons/backend/app/api/v1/endpoints/files.py', 'w') as f:
    f.write(content)
