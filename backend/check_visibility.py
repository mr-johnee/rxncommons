from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.crud import crud_dataset
from app.models.dataset import Dataset, DatasetVersion
from app.core.dataset_access import PUBLIC_VISIBLE_STATUSES

engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

print(f"PUBLIC_VISIBLE_STATUSES in dataset_access: {PUBLIC_VISIBLE_STATUSES}")

# Check raw datasets
datasets = db.query(Dataset).all()
print(f"Total datasets in DB: {len(datasets)}")
for d in datasets:
    print(f"ID: {d.id}, Title: {d.title}, Status: {d.dataset_status}, CurrentVer: {d.current_version}")
    # print(f"ID: {d.id}, Title: {d.title}, Status: {d.dataset_status}, Access: {d.access_level}")
    versions = db.query(DatasetVersion).filter(DatasetVersion.dataset_id == d.id).all()
    for v in versions:
        print(f"  - Version {v.version_num}: {v.status}")

# Test get_datasets
print("\nTesting get_datasets...")
items, total = crud_dataset.get_datasets(db, limit=10, include_private=False)
print(f"get_datasets returned {total} items")
for item in items:
    print(f" - {item.title} ({item.dataset_status}), Rows: {getattr(item, 'total_rows', 'N/A')}")

db.close()
