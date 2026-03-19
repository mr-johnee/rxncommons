import urllib.request, json

# 测试创建数据集流程
try:
    print(">>> 1. 登录现有账号获取 Token")
    data = json.dumps({'email': 'test7@example.com', 'password': 'securepassword123'}).encode()
    req = urllib.request.Request('http://127.0.0.1:8000/api/auth/login', data=data, headers={'Content-Type': 'application/json'})
    res = urllib.request.urlopen(req)
    login_info = json.loads(res.read())
    access_token = login_info['access_token']
    user_id = login_info['user']['id']
    print("✅ Token获取成功")

    print("\n>>> 2. 【被拦截测试】直接尝试创建数据集，应该提示邮箱未验证（403）...")
    try:
        ds_data = json.dumps({"title": "My Awesome Reaction Dataset", "description": "some info"}).encode()
        req_ds = urllib.request.Request('http://127.0.0.1:8000/api/datasets', data=ds_data, headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {access_token}'})
        urllib.request.urlopen(req_ds)
    except urllib.error.HTTPError as e:
        err_msg = json.loads(e.read())
        print(f"✅ 符合预期被拦截，报错为: {e.code}  detail: {err_msg}")
    
    print("\n>>> 3. [后台模拟] 在数据库中把此用户 `is_email_verified` 改为 True")
    from sqlalchemy import create_engine, text
    from app.core.config import settings
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
    with engine.connect() as conn:
        conn.execute(text(f"UPDATE users SET is_email_verified = true WHERE id = '{user_id}'"))
        conn.commit()
    print("✅ 修改为已激活状态")
    
    print("\n>>> 4. 再次尝试创建数据集")
    ds_data_1 = json.dumps({"title": "My Awesome #Reaction! (Data) set", "description": "This is a base reaction dataset.", "source_type": "lab"}).encode()
    req_ds_1 = urllib.request.Request('http://127.0.0.1:8000/api/datasets', data=ds_data_1, headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {access_token}'})
    res_ds_1 = urllib.request.urlopen(req_ds_1)
    dataset1 = json.loads(res_ds_1.read())
    print("✅ 第一个数据集创建成功！")
    print(f"生成的 Slug 是:  {dataset1['slug']}")
    print(f"数据集状态是: {dataset1['dataset_status']}")
    print(f"当前指针处于: V{dataset1['current_version']}")
    
    print("\n>>> 5. 测试同名下的 Slug 冲突自动增长机制")
    ds_data_2 = json.dumps({"title": "My Awesome #Reaction! (Data) set", "description": "Another copy of same dataset."}).encode()
    req_ds_2 = urllib.request.Request('http://127.0.0.1:8000/api/datasets', data=ds_data_2, headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {access_token}'})
    res_ds_2 = urllib.request.urlopen(req_ds_2)
    dataset2 = json.loads(res_ds_2.read())
    print("✅ 第二个数据集创建成功！")
    print(f"它处理完冲突后被自动分配的 Slug 是:  {dataset2['slug']}")

except Exception as e:
    import traceback
    traceback.print_exc()
