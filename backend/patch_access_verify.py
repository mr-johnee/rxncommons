with open('/home/zy/zhangyi/rxncommons/backend/app/core/dataset_access.py', 'r') as f:
    content = f.read()

old_str_verify = """def verify_dataset_access_password(db: Session, dataset: Dataset, password: str) -> bool:
    policy = get_dataset_access_policy(db, dataset.id)
    if not policy or policy.access_level != ACCESS_LEVEL_PASSWORD_PROTECTED:
        return False
    if not policy.password_hash:
        return False
    return verify_password(password, policy.password_hash)"""

new_str_verify = """def verify_dataset_access_password(db: Session, dataset: Dataset, password: str) -> bool:
    policy = get_dataset_access_policy(db, dataset.id)
    if not policy or policy.access_level != ACCESS_LEVEL_PASSWORD_PROTECTED:
        return False
    if not policy.password_hash:
        return False
    # Backward compatibility with existing bcrypt hashes
    if policy.password_hash.startswith("$2b$"):
        return verify_password(password, policy.password_hash)
    # Direct comparison if stored as plain text
    return password == policy.password_hash"""

old_str_set = """    if access_level == ACCESS_LEVEL_PUBLIC:
        policy.password_hash = None
    else:
        next_password = (access_password or "").strip()
        if next_password:
            if len(next_password) < 6:
                raise ValueError("access_password_too_short")
            policy.password_hash = get_password_hash(next_password)
        elif not policy.password_hash:
            raise ValueError("missing_access_password")"""

new_str_set = """    if access_level == ACCESS_LEVEL_PUBLIC:
        policy.password_hash = None
    else:
        next_password = (access_password or "").strip()
        if next_password:
            # We skip the minimum length requirement specifically for auto-generating
            policy.password_hash = next_password
        elif not policy.password_hash:
            raise ValueError("missing_access_password")"""

content = content.replace(old_str_verify, new_str_verify)
content = content.replace(old_str_set, new_str_set)
with open('/home/zy/zhangyi/rxncommons/backend/app/core/dataset_access.py', 'w') as f:
    f.write(content)
