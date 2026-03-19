import requests
import uuid
import os
from sqlalchemy import create_engine, text

BASE_URL = "http://localhost:8000/api"
DB_URL = "postgresql://rxn_user:rxn_pass_123@localhost:5433/rxncommons"
engine = create_engine(DB_URL)

uid = uuid.uuid4().hex[:6]
username = f"usr_{uid}"
email = f"{username}@test.com"
password = "password123"

# 1. Register & Login
requests.post(f"{BASE_URL}/auth/register", json={"username":username, "email":email, "password":password})
res = requests.post(f"{BASE_URL}/auth/login", json={"email":email, "password":password})
token = res.json()["access_token"]
user_id = res.json()["user"]["id"]

# Verify email
with engine.connect() as conn:
    conn.execute(text(f"UPDATE users SET is_email_verified = true WHERE id = '{user_id}'"))
    conn.commit()

headers = {"Authorization": f"Bearer {token}"}

# 2. Create Dataset
ds_res = requests.post(f"{BASE_URL}/datasets", headers=headers, json={"title":f"Test Dataset {uid}"})
dataset_id = ds_res.json()["id"]
print(f"Dataset created: {dataset_id}")

# 3. Test Upvote
upvote_res = requests.post(f"{BASE_URL}/datasets/{dataset_id}/upvote", headers=headers)
print("Upvote:", upvote_res.status_code, upvote_res.json())

# 4. Test Discussions
disc_res = requests.post(f"{BASE_URL}/datasets/{dataset_id}/discussions", headers=headers, json={"content":"Great dataset!"})
print("Discussion created:", disc_res.status_code, disc_res.json())
disc_list = requests.get(f"{BASE_URL}/datasets/{dataset_id}/discussions")
print("Discussion list:", disc_list.status_code, len(disc_list.json()), "items")

# 5. Submit review
rev_res = requests.post(f"{BASE_URL}/datasets/{dataset_id}/submit-review", headers=headers, json={"version_num": 1})
print("Submit review:", rev_res.status_code, rev_res.json())

# Verify status in DB
with engine.connect() as conn:
    row = conn.execute(text(f"SELECT dataset_status FROM datasets WHERE id = '{dataset_id}'")).fetchone()
    print("Dataset Status in DB:", row[0])

