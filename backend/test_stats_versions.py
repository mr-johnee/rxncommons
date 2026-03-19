import requests
import uuid
from sqlalchemy import create_engine, text

BASE_URL = "http://localhost:8000/api"
DB_URL = "postgresql://rxn_user:rxn_pass_123@localhost:5433/rxncommons"
engine = create_engine(DB_URL)

uid = uuid.uuid4().hex[:6]
username = f"statusr_{uid}"
email = f"{username}@test.com"
password = "password123"

requests.post(f"{BASE_URL}/auth/register", json={"username":username, "email":email, "password":password})
res = requests.post(f"{BASE_URL}/auth/login", json={"email":email, "password":password})
token = res.json()["access_token"]
user_id = res.json()["user"]["id"]

with engine.connect() as conn:
    conn.execute(text(f"UPDATE users SET is_email_verified = true WHERE id = '{user_id}'"))
    conn.commit()

headers = {"Authorization": f"Bearer {token}"}

ds_res = requests.post(f"{BASE_URL}/datasets", headers=headers, json={"title":f"Test Fetch {uid}"})
dataset = ds_res.json()
dataset_id = dataset["id"]
slug = dataset["slug"]

# Get list
list_res = requests.get(f"{BASE_URL}/datasets")
print("List count:", list_res.json()["total"])

# Get detail
detail_res = requests.get(f"{BASE_URL}/datasets/{username}/{slug}")
print("Detail id:", detail_res.json()["id"])

# Stats
stats_res = requests.get(f"{BASE_URL}/stats/overview")
print("Stats:", stats_res.json())

# Create version
v_res = requests.post(f"{BASE_URL}/datasets/{dataset_id}/versions", headers=headers, json={"base_version_num": 1})
print("Version create:", v_res.status_code, v_res.text)

# List versions
v_list_res = requests.get(f"{BASE_URL}/datasets/{dataset_id}/versions")
print("List versions:", v_list_res.json())

