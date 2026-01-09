import logging

import httpx
import xmltodict
from fastapi import APIRouter, Request, Form

from config import SMS_API_URL, ENTERPRISE_ID, USERNAME, PASSWORD_MD516

logger = logging.getLogger(__name__)
router = APIRouter()


# 1.1. 短信发送方法 1
# 测试命令：Invoke-WebRequest -Uri 'http://localhost:8000/api/sendSmsV1' -Method POST -ContentType 'application/x-www-form-urlencoded' -Body 'phone_numbers=15144042132&message=测试短信&msg_id=123456&ext=test'
@router.post("/sendSmsV1")
async def sendSmsV1(phone_numbers: str = Form(...), message: str = Form(...), msg_id: str = Form(None),
                    ext: str = Form(None)):
    # 校验手机号数量，最多接收50个
    phone_list = phone_numbers.split(',')
    if len(phone_list) > 50:
        return {"status": "error", "message": "手机号数量不能超过50个",
                "requestParam": {"phone_numbers": phone_numbers, "message": message, "msg_id": msg_id, "ext": ext}}

    # 构建请求参数
    params = {
        "f": "2",
        "uid": ENTERPRISE_ID,
        "un": USERNAME,
        "pw": PASSWORD_MD516,
        "p": phone_numbers,
        "i": message.encode('utf-8')
    }

    # 添加可选参数
    if ext:
        params["s"] = ext
    if msg_id:
        params["t"] = msg_id

    # 发送请求
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(SMS_API_URL, params=params, timeout=10.0)
            response.raise_for_status()
            return {"status": "success", "result": response.text,
                    "requestParam": {"phone_numbers": phone_numbers, "message": message, "msg_id": msg_id, "ext": ext}}
        except Exception as e:
            return {"status": "error", "message": str(e),
                    "requestParam": {"phone_numbers": phone_numbers, "message": message, "msg_id": msg_id, "ext": ext}}


# 1.2. 短信发送方法 2（批量发送）
# 测试命令：$xmlData = "<SmsList><row phone='15144042132' info='测试短信内容' spnumber='test' msgid='123456' /><row phone='13800138000' info='测试短信内容' spnumber='test' msgid='123456' /></SmsList>"; Invoke-WebRequest -Uri 'http://localhost:8000/api/sendSmsV2' -Method POST -ContentType 'application/x-www-form-urlencoded' -Body "xml_data=$xmlData"
@router.post("/sendSmsV2")
async def sendSmsV2(xml_data: str = Form(...)):
    # 打印接收到的请求参数
    print(f"[sendSmsV2] 接收到的XML数据: {xml_data}")

    try:
        # 解析XML数据
        data = xmltodict.parse(xml_data)
        sms_list = data.get("SmsList", {})
        rows = sms_list.get("row", [])

        # 处理单条或多条数据
        if not isinstance(rows, list):
            rows = [rows]

        # 检查row节点数量是否超过50个
        if len(rows) > 50:
            return {"status": "error", "message": "XML中最多只能包含50个row节点",
                    "requestParam": {"xml_data": xml_data}}

        # 构建请求参数
        params = {
            "f": "3",
            "uid": ENTERPRISE_ID,
            "un": USERNAME,
            "pw": PASSWORD_MD516,
            "i": xml_data
        }

        print(f"[sendSmsV2] 请求方式: GET")
        print(f"[sendSmsV2] 请求地址: {SMS_API_URL}")
        print(f"[sendSmsV2] 请求参数: {params}")

        # 发送请求
        async with httpx.AsyncClient() as client:
            response = await client.get(SMS_API_URL, params=params, timeout=10.0)
            response.raise_for_status()
            print(f"[send-sms-v2] 响应状态码: {response.status_code}")
            print(f"[send-sms-v2] 响应内容: {response.text}")

            return {"status": "success", "result": response.text, "requestParam": {"xml_data": xml_data}}
    except Exception as e:
        print(f"[send-sms-v2] 请求失败: {str(e)}")
        return {"status": "error", "message": str(e), "requestParam": {"xml_data": xml_data}}


# 1.3. 获取余额
# 测试命令：Invoke-WebRequest -Uri 'http://localhost:8000/api/balance' -Method GET
@router.get("/balance")
async def balance():
    # 构建请求参数
    params = {
        "f": "4",
        "uid": ENTERPRISE_ID,
        "un": USERNAME,
        "pw": PASSWORD_MD516
    }

    print(f"[balance] 请求方式: GET")
    print(f"[balance] 请求地址: {SMS_API_URL}")
    print(f"[balance] 请求参数: {params}")
    # http://61.191.26.189:8888/smser.ashx?f=4&uid=71895&un=ccznkf&pw=a7ffa0251a4268f2

    # 发送请求
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(SMS_API_URL, params=params, timeout=10.0)
            response.raise_for_status()
            #
            print(f"[balance] response: {response}")
            print(f"[balance] 响应 url: {response.url}")
            print(f"[balance] 响应 status_code: {response.status_code}")
            print(f"[balance] 响应 content: {response.content}")
            print(f"[balance] 响应头 headers: {dict(response.headers)}")
            print(f"[balance] 响应内容 text: {response.text}")
            return {"status": "success", "balance": response.text}
            # return {"status": "success", "balance": "0000"}
        except Exception as e:
            print(f"[balance] 请求失败: {str(e)}")
            return {"status": "error", "message": str(e)}


# 1.4. 接收推送上行数据
# 测试命令：$xmlData = "<MOList><MORow Phone='13800138000' MOInfo='测试上行内容' SpNumber='001' MO_Time='2026-01-08 11:11:11' /></MOList>"; Invoke-WebRequest -Uri 'http://localhost:8000/api/pushUp' -Method POST -ContentType 'text/xml' -Body $xmlData
@router.post("/pushUp")
async def pushUp(request: Request):
    # 读取请求体 XML 数据
    xml_content = await request.body()
    print(f"[pushUp] 接收到上行短信推送，XML 内容: {xml_content.decode('utf-8')}")

    # 解析 XML
    try:
        data = xmltodict.parse(xml_content)
        mo_list = data.get("MOList", {})
        mo_rows = mo_list.get("MORow", [])
        # 处理单条或多条数据
        if not isinstance(mo_rows, list):
            mo_rows = [mo_rows]

        # 转换为JSON数组
        reports = []
        for row in mo_rows:
            status_report = {
                "Phone": row.get("@Phone"),
                "MOInfo": row.get("@MOInfo"),
                "SpNumber": row.get("@SpNumber"),
                "MO_Time": row.get("@MO_Time"),
            }
            reports.append(status_report)

        # 输出到控制台
        print(f"[pushStatus] 状态报告JSON数组: {reports}")

        return {"status": "success", "requestBody": reports}
    except Exception as e:
        print(f"[pushUp] XML 解析失败: {str(e)}")
        return {"status": "error", "message": f"XML 解析失败: {str(e)}"}


# 1.5. 接收推送状态报告
# 测试命令：$xmlData = "<?xml version='1.0' encoding='utf-8'?><MRList><MRRow Phone='13800138000' Report='0' MsgID='123456789' SpNumber='' Report_Time='2026-01-08 11:11:11' Record_Time='2026-01-08 10:10:10' /></MRList>"; Invoke-WebRequest -Uri 'http://localhost:8000/api/pushStatus' -Method POST -ContentType 'text/xml' -Body $xmlData
@router.post("/pushStatus")
async def pushStatus(request: Request):
    # 读取请求体 XML 数据
    xml_content = await request.body()
    print(f"[pushStatus] 接收到状态报告推送，XML 内容: {xml_content.decode('utf-8')}")

    # 解析 XML
    try:
        data = xmltodict.parse(xml_content)
        mr_list = data.get("MRList", {})
        mr_rows = mr_list.get("MRRow", [])
        # 处理单条或多条数据
        if not isinstance(mr_rows, list):
            mr_rows = [mr_rows]

        # 转换为JSON数组
        reports = []
        for row in mr_rows:
            status_report = {
                "Phone": row.get("@Phone"),
                "Report": row.get("@Report"),
                "MsgID": row.get("@MsgID"),
                "SpNumber": row.get("@SpNumber"),
                "Report_Time": row.get("@Report_Time"),
                "Record_Time": row.get("@Record_Time")
            }
            reports.append(status_report)

        # 输出到控制台
        print(f"[pushStatus] 状态报告JSON数组: {reports}")

        return {"status": "success", "requestBody": reports}

    except Exception as e:
        print(f"[pushStatus] XML 解析失败: {str(e)}")
        # 即使解析失败也返回0给推送者
        return "0"
