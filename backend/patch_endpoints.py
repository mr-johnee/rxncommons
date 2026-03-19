import re

with open('/home/zy/zhangyi/rxncommons/backend/app/api/v1/endpoints/datasets.py', 'r') as f:
    content = f.read()

# For getting dataset by id: include password
content = re.sub(
    r'attach_access_level\(dataset, get_dataset_access_policy\(db, dataset\.id\)\)', 
    r'attach_access_level(dataset, get_dataset_access_policy(db, dataset.id), include_password=is_owner_or_admin)', 
    content, count=1   # Assuming the first one or we can just replace the specific one
)

with open('/home/zy/zhangyi/rxncommons/backend/app/api/v1/endpoints/datasets.py', 'w') as f:
    f.write(content)
