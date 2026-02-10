import requests
# ==================================================================
# 测试数据 @router.post("/sendSmsV1")
data = {
    'phone_numbers': '15643117897',
    'message': '测试短信',
    'msg_id': '123456',
    'ext': 'test'
}

# 发送POST请求
response = requests.post(
    'http://116.141.0.77:5678/api/sendSmsV1',
    data=data,
    headers={'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'}
)

# 打印响应
print('1.1. 短信发送方法1 sendSmsV1')
print('请求内容:', data)
print('状态码:', response.status_code)
print('响应内容:', response.text)

# ==================================================================
# 测试数据 @router.post("/sendSmsV2")
xml_data = "<SmsList><row phone='15643117897' info='测试短信内容' spnumber='test' msgid='123456' /><row phone='13800138000' info='测试短信内容' spnumber='test' msgid='123456' /></SmsList>"

# 发送POST请求
response = requests.post(
    'http://116.141.0.77:5678/api/sendSmsV2',
    data={'xml_data': xml_data},
    headers={'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'}
)

# 打印响应
print('\n1.2. 短信发送方法2  /api/sendSmsV2')
print('请求内容:', xml_data)
print('状态码:', response.status_code)
print('响应内容:', response.text)

# ==================================================================
# 测试数据 @router.get("/balance")

# 发送GET请求
response = requests.get(
    'http://localhost:8000/api/balance'
)

# 打印响应
print('\n1.3. 获取余额  /api/balance')
print('请求内容:无')
print('状态码:', response.status_code)
print('响应内容:', response.text)

# ==================================================================
# 测试数据 @router.post("/pushUp")
push_up_xml = "<MOList><MORow Phone='13800138000' MOInfo='测试上行内容' SpNumber='001' MO_Time='2026-01-08 11:11:11' /></MOList>"

# 发送POST请求
response = requests.post(
    'http://localhost:8000/api/pushUp',
    data=push_up_xml,
    headers={'Content-Type': 'text/xml; charset=utf-8'}
)

# 打印响应
print('\n1.4. 接收推送上行数据  /api/pushUp')
print('请求内容 Body:',push_up_xml)
print('状态码:', response.status_code)
print('响应内容:', response.text)

# ==================================================================
# 测试数据 @router.post("/pushStatus")
push_status_xml = "<?xml version='1.0' encoding='utf-8'?><MRList><MRRow Phone='13800138000' Report='0' MsgID='123456789' SpNumber='' Report_Time='2026-01-08 11:11:11' Record_Time='2026-01-08 10:10:10' /></MRList>"

# 发送POST请求
response = requests.post(
    'http://localhost:8000/api/pushStatus',
    data=push_status_xml,
    headers={'Content-Type': 'text/xml; charset=utf-8'}
)

# 打印响应
print('\n1.5. 接收推送状态报告  /api/pushStatus')
print('请求内容 Body:',push_status_xml)
print('状态码:', response.status_code)
print('响应内容:', response.text)
