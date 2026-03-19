import sys
import os
from sqlalchemy import create_engine, inspect, text

# Add backend directory to sys.path
backend_path = os.path.abspath(os.path.join(os.getcwd(), 'rxncommons/backend'))
sys.path.append(backend_path)

from app.core.config import settings

def check_db():
    print(f"Connecting to {settings.SQLALCHEMY_DATABASE_URI}")
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
    try:
        inspector = inspect(engine)
        columns = inspector.get_columns('dataset_versions')
        column_names = [c['name'] for c in columns]
        print(f"Columns in dataset_versions: {column_names}")
        
        if 'archive_key' in column_names:
            print("SUCCESS: archive_key column exists in database.")
        else:
            print("FAILURE: archive_key column DOES NOT exist in database.")
            
    except Exception as e:
        print(f"Error checking DB: {e}")

if __name__ == "__main__":
    check_db()
