import requests
import os
import uuid
import time
from sqlalchemy import create_engine, text

BASE_URL = "http://localhost:8000/api"
DB_URL = "postgresql://rxn_user:rxn_pass_123@localhost:5433/rxncommons"
engine = create_engine(DB_URL)

unique_id = uuid.uuid4().hex[:6]
email = f"fileuser_{unique_id}@example.com"
password = "filepassword123"
username = f"fileuser_{unique_id}"

# 1. Register
res = requests.post(f"{BASE_URL}/auth/register", json={
    "username": username,
    "email": email,
    "password": password
})
print("Register response:", res.status_code)

# 2. Login
res = requests.post(f"{BASE_URL}/auth/login", json={
    "email": email,
    "password": password
})
token = res.json()["access_token"]
user_id = res.json()["user"]["id"]

# 3. Simulate email verified
with engine.connect() as conn:
    conn.execute(text(f"UPDATE users SET is_email_verified = true WHERE id = '{user_id}'"))
    conn.commit()

headers = {"Authorization": f"Bearer {token}"}

# 4. Create Dataset
ds_res = requests.post(f"{BASE_URL}/datasets", headers=headers, json={
    "title": "Module B File Test",
    "description": "Testing file uploads"
})
print("Create Dataset:", ds_res.status_code, ds_res.json())
dataset_id = ds_res.json()["id"]

# 5. Upload File
test_file_path = "mini_sample.txt"
with open(test_file_path, "wb") as f:
    f.write(b"Hello from Module B file upload testing!")

url = f"{BASE_URL}/datasets/{dataset_id}/files"
with open(test_file_path, "rb") as f:
    files = {"file": ("mini_sample.txt", f, "text/plain")}
    data = {"version_num": 1}
    upload_response = requests.post(url, headers=headers, files=files, data=data)

print("Upload response:", upload_response.status_code)
print(upload_response.text)

# Cleanup
os.remove(test_file_path)
