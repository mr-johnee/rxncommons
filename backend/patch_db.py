from sqlalchemy import create_engine, text
from app.core.config import settings

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
with engine.connect() as con:
    con.execute(text("ALTER TABLE dataset_versions ADD COLUMN archive_key VARCHAR(500);"))
    con.commit()
    print("Added")
