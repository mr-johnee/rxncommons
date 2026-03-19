import requests
import os
import uuid
import time
from sqlalchemy import create_engine, text

BASE_URL = "http://localhost:8000/api"
DB_URL = "postgresql://rxn_user:rxn_pass_123@localhost:5433/rxncommons"
engine = create_engine(DB_URL)

email = f"admin_{uuid.uuid4().hex[:6]}@test.com"
password = "adminpassword123"

# Register & Login
requests.post(f"{BASE_URL}/auth/register", json={"username": email.split('@')[0], "email": email, "password": password})
res = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
token = res.json()["access_token"]
user_id = res.json()["user"]["id"]

with engine.connect() as conn:
    conn.execute(text(f"UPDATE users SET is_email_verified = true, role = 'admin' WHERE id = '{user_id}'"))
    conn.commit()

headers = {"Authorization": f"Bearer {token}"}

# Create Dataset
ds_res = requests.post(f"{BASE_URL}/datasets", headers=headers, json={"title": "Test Archiving Features", "description": "Testing ZIP packaging"})
dataset_id = ds_res.json()["id"]

# Upload a file
with open("test_mock.csv", "wb") as f:
    f.write(b"col1,col2\n1,2\n3,4")

with open("test_mock.csv", "rb") as f:
    upload_res = requests.post(f"{BASE_URL}/datasets/{dataset_id}/files", headers=headers, files={"file": ("test_mock.csv", f, "text/csv")}, data={"version_num": 1})
file_id = upload_res.json()["id"]

print("Upload Success:", upload_res.status_code)

# Download single file test
down_res = requests.get(f"{BASE_URL}/datasets/{dataset_id}/files/{file_id}/download", headers=headers)
print("Single file download url (should contain presigned url):", down_res.json())

# Submit Review
res = requests.post(f"{BASE_URL}/datasets/{dataset_id}/submit-review", json={"version_num": 1}, headers=headers)
print("Submit review:", res.status_code, res.text)

# Get review requests
rev_res = requests.get(f"{BASE_URL}/admin/review-requests", headers=headers)
req_id = [r for r in print(rev_res.text) or rev_res.json() if r['dataset_id'] == dataset_id][0]['id']

# Admin Approve -> Triggers Packaging
app_res = requests.post(f"{BASE_URL}/admin/review-requests/{req_id}/approve", headers=headers)
print("Admin Approve:", app_res.status_code, app_res.text)

time.sleep(2) # Give background task time to zip and upload

# Download All
down_all_res = requests.get(f"{BASE_URL}/datasets/{dataset_id}/versions/1/download-all", headers=headers)
print("Download All res:", down_all_res.status_code, down_all_res.text)
