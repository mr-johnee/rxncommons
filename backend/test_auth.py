import urllib.request, json
try:
    # 1. Login
    data = json.dumps({'email': 'test7@example.com', 'password': 'securepassword123'}).encode()
    req = urllib.request.Request('http://127.0.0.1:8000/api/auth/login', data=data, headers={'Content-Type': 'application/json', 'accept': 'application/json'})
    res = urllib.request.urlopen(req)
    login_res = json.loads(res.read())
    print('✅ 登录成功，获取到 Access Token 和 Refresh Token')
    access_token = login_res['access_token']
    refresh_token = login_res['refresh_token']
    
    # 2. 获取本人信息 /users/me
    req_me = urllib.request.Request('http://127.0.0.1:8000/api/users/me', headers={'Authorization': f'Bearer {access_token}', 'accept': 'application/json'})
    res_me = urllib.request.urlopen(req_me)
    me_res = json.loads(res_me.read())
    print('✅ 成功访问受保护接口 /api/users/me! 当前访问者为:', me_res['email'])
    
    # 3. 兑换新 Token
    refresh_data = json.dumps({'refresh_token': refresh_token}).encode()
    req_ref = urllib.request.Request('http://127.0.0.1:8000/api/auth/refresh', data=refresh_data, headers={'Content-Type': 'application/json', 'accept': 'application/json'})
    res_ref = urllib.request.urlopen(req_ref)
    ref_res = json.loads(res_ref.read())
    print('✅ 成功使用 Refresh Token 换取了新的 Token 对！')
    new_access = ref_res['access_token']
    
    # 4. 退销 Token /logout
    req_logout = urllib.request.Request('http://127.0.0.1:8000/api/auth/logout', data=b'', headers={'Authorization': f'Bearer {new_access}', 'accept': 'application/json'})
    res_logout = urllib.request.urlopen(req_logout)
    print('✅ 成功访问 /api/auth/logout，结果:', json.loads(res_logout.read()))

except Exception as e:
    import traceback
    traceback.print_exc()
