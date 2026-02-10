from contextlib import asynccontextmanager
from typing import List

import httpx
import xmltodict
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import APIRouter, Request, Body, Depends

from auth import verify_token
from sys_logger import setup_logger
from model import ApiResponse, SendSmsV1Request, SmsItem
from util import md5_encrypt_16_lower, getConfig, escape_xml

router = APIRouter()
logger = setup_logger()

logger.info(f"[CONFIG]  {getConfig()} ")


# 1.1. 短信发送方法 1
@router.post("/sendSmsV1", response_model=ApiResponse)
async def sendSmsV1(data: SendSmsV1Request = Body(...), token: str = Depends(verify_token)):
    # 打印接收到的请求参数
    logger.info(f"[sendSmsV1] 入参: {data.dict()}")

    # 提取参数
    phone_numbers = data.phone_numbers
    msg_id = data.msg_id
    ext = data.ext

    # 构建请求参数
    params = {
        "f": "2",
        "uid": getConfig()["ENTERPRISE_ID"],
        "un": getConfig()["USERNAME"],
        "pw": md5_encrypt_16_lower(getConfig()["PASSWORD"]),
        "p": phone_numbers,
        "i": getConfig()["MSG_CONTENT"]
    }

    # 添加可选参数
    if ext:
        params["s"] = ext
    if msg_id:
        params["t"] = msg_id

    # 发送请求
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(getConfig()["SMS_API_URL"], params=params, timeout=10.0)
            # 记录实际发起的完整请求信息
            actual_request = response.request
            logger.info(
                f"[sendSmsV1] 实际发起请求: {actual_request.method} {actual_request.url} 头信息: {dict(actual_request.headers)}")
            response.raise_for_status()
            logger.info(f"[sendSmsV1] 响应状态码:{response.status_code}  响应结果:{response.text}")
            return ApiResponse(
                status="success",
                result=response.text,
            )
        except Exception as e:
            logger.info(f"[sendSmsV1] 请求异常: {str(e)}")
            return ApiResponse(
                status="error",
                message=str(e),
            )


# 1.2. 短信发送方法 2（批量发送）
@router.post("/sendSmsV2", response_model=ApiResponse)
async def sendSmsV2(data: List[SmsItem] = Body(...), token: str = Depends(verify_token)):
    # 打印接收到的请求参数
    logger.info(f"[sendSmsV2] 入参: {[item.dict() for item in data]}")

    try:
        # 检查数据数量是否超过50个
        if len(data) > 50:
            return ApiResponse(
                status="error",
                message="最多只能发送50条短信",
            )

        # 将JSON数组转换为XML格式
        info = getConfig()["MSG_CONTENT"]

        xml_data = "<SmsList>"
        for item in data:
            _info = escape_xml(item.info) if item.info else info
            xml_data += f"<row phone='{item.phone}' info='{_info}' spnumber='{item.spnumber}' msgid='{item.msgid}' />"
        xml_data += "</SmsList>"

        # 构建请求参数
        params = {
            "f": "3",
            "uid": getConfig()["ENTERPRISE_ID"],
            "un": getConfig()["USERNAME"],
            "pw": md5_encrypt_16_lower(getConfig()["PASSWORD"]),
            "i": xml_data
        }

        # 发送请求
        async with httpx.AsyncClient() as client:
            # 使用data而不是json，避免字节类型序列化错误
            response = await client.post(getConfig()['SMS_API_URL'], params=params, timeout=10.0)
            # 记录实际发起的完整请求信息
            actual_request = response.request
            logger.info(
                f"[sendSmsV2] 实际发起请求: {actual_request.method} {actual_request.url} 头信息: {dict(actual_request.headers)}")
            response.raise_for_status()
            logger.info(f"[sendSmsV2] 响应状态码:{response.status_code}  响应结果:{response.text}")
            return ApiResponse(
                status="success",
                result=response.text,
            )
    except Exception as e:
        logger.info(f"[sendSmsV2] 请求失败: {str(e)}")
        return ApiResponse(
            status="error",
            message=str(e),
        )


# 1.3. 获取余额
@router.get("/balance", response_model=ApiResponse)
async def balance(token: str = Depends(verify_token)):
    # 构建请求参数
    params = {
        "f": "4",
        "uid": getConfig()["ENTERPRISE_ID"],
        "un": getConfig()["USERNAME"],
        "pw": md5_encrypt_16_lower(getConfig()["PASSWORD"])
    }

    # 发送请求
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(getConfig()['SMS_API_URL'], params=params, timeout=10.0)
            # 记录实际发起的完整请求信息
            actual_request = response.request
            logger.info(
                f"[balance] 实际发起请求: {actual_request.method} {actual_request.url} 头信息: {dict(actual_request.headers)}")
            response.raise_for_status()
            logger.info(f"[balance] 响应状态码:{response.status_code}  响应结果:{response.text}")

            return ApiResponse(status="success", result=response.text)
        except Exception as e:
            logger.info(f"[balance] 请求失败: {str(e)}")
            return ApiResponse(
                status="error",
                message=str(e)
            )


# 1.4. 接收推送上行数据
@router.post("/pushUp", response_model=ApiResponse)
async def pushUp(request: Request, token: str = Depends(verify_token)):
    # 读取请求体 XML 数据
    xml_content = await request.body()
    logger.info(f"[pushUp] 接收到上行短信推送，XML 内容: {xml_content.decode('utf-8')}")

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
        logger.info(f"[pushUp] 状态报告JSON数组: {reports}")

        return ApiResponse(
            status="success",
        )
    except Exception as e:
        logger.info(f"[pushUp] XML 解析失败: {str(e)}")
        return ApiResponse(
            status="error",
            message=f"XML 解析失败: {str(e)}"
        )


# 1.5. 接收推送状态报告
@router.post("/pushStatus")
async def pushStatus(request: Request, token: str = Depends(verify_token)):
    # 读取请求体 XML 数据
    xml_content = await request.body()
    logger.info(f"[pushStatus] 接收到状态报告推送，XML 内容: {xml_content.decode('utf-8')}")

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
        logger.info(f"[pushStatus] 状态报告JSON数组: {reports}")

        return ApiResponse(
            status="success",
        )

    except Exception as e:
        logger.info(f"[pushStatus] XML 解析失败: {str(e)}")
        # 即使解析失败也返回0给推送者
        return "0"


# 定时任务：检查短信余额并发送通知
async def check_balance_and_notify():
    logger.info("[定时任务] 开始执行余额检查...")
    try:
        # 1. 调用余额查询接口
        async with httpx.AsyncClient() as client:
            # 构建请求参数
            params = {
                "f": "4",
                "uid": getConfig()["ENTERPRISE_ID"],
                "un": getConfig()["USERNAME"],
                "pw": md5_encrypt_16_lower(getConfig()["PASSWORD"])
            }

            response = await client.get(getConfig()["SMS_API_URL"], params=params, timeout=10.0)
            # 记录实际发起的完整请求信息
            actual_request = response.request
            logger.info(
                f"[定时任务] 实际发起余额查询请求: {actual_request.method} {actual_request.url} 头信息: {dict(actual_request.headers)}")
            response.raise_for_status()
            balance = response.text.strip()

            logger.info(f"[定时任务] 余额查询结果: {balance}")

            # 2. 检查余额是否低于配置 ALARM_COUNT
            try:
                balance_num = int(balance)
                ALARM_COUNT = getConfig()["ALARM_COUNT"]
                if balance_num < ALARM_COUNT:
                    logger.info(f"[定时任务] 余额不足 ({balance_num}<{ALARM_COUNT} )，开始发送通知...")

                    # 3. 发送短信通知
                    notify_phone = getConfig()["ALARM_PHONE"]
                    template = getConfig().get(
                        "ALARM_CONTENT",
                        "短信剩余数量告警：您的短信剩余{balance_num}条，请及时充值！"
                    )
                    message = template.format(balance_num=balance_num)

                    # 构建发送短信的参数
                    sms_params = {
                        "f": "2",
                        "uid": getConfig()["ENTERPRISE_ID"],
                        "un": getConfig()["USERNAME"],
                        "pw": md5_encrypt_16_lower(getConfig()["PASSWORD"]),
                        "p": notify_phone,
                        "i": message
                    }

                    sms_response = await client.get(getConfig()["SMS_API_URL"], params=sms_params, timeout=10.0)
                    # 记录实际发起的完整请求信息
                    actual_sms_request = sms_response.request
                    logger.info(
                        f"[定时任务] 实际发起通知短信请求: {actual_sms_request.method} {actual_sms_request.url} 头信息: {dict(actual_sms_request.headers)}")
                    sms_response.raise_for_status()

                    logger.info(f"[定时任务] 通知发送成功，响应结果: {sms_response.text}")
                else:
                    logger.info(f"[定时任务] 余额充足 ({balance_num} >= {ALARM_COUNT})，无需通知")
            except ValueError:
                logger.error(f"[定时任务] 余额解析失败: {balance}")

    except Exception as e:
        logger.error(f"[定时任务] 执行失败: {str(e)}")


# FastAPI 生命周期管理
@asynccontextmanager
async def lifespan(app):
    """管理 FastAPI 应用的生命周期"""
    global scheduler

    # 启动时初始化调度器
    logger.info("[启动] 初始化定时任务调度器...")
    scheduler = AsyncIOScheduler()

    # 添加定时任务，从配置文件读取执行频率
    cron_expression = getConfig()["ALARM_CRON"]
    scheduler.add_job(
        check_balance_and_notify,
        trigger=CronTrigger.from_crontab(cron_expression),
        name="check_sms_balance"
    )

    # 启动调度器
    scheduler.start()
    logger.info(f"[启动] 定时任务已启动，执行频率: {cron_expression}")

    yield

    # 关闭时清理调度器
    logger.info("[关闭] 正在关闭定时任务调度器...")
    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info("[关闭] 调度器已关闭")


# 路由定义
@router.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "scheduler_running": scheduler.running if scheduler else False}

# # 初始化调度器
# scheduler = AsyncIOScheduler()
#
# # 添加定时任务，从配置文件读取执行频率
# cron_expression = getConfig()["ALARM_CRON"]
# scheduler.add_job(
#     check_balance_and_notify,
#     trigger=CronTrigger.from_crontab(cron_expression),
#     name="check_sms_balance"
# )
#
# # 启动调度器
# scheduler.start()
# logger.info(f"[定时任务] 已启动，执行频率: {cron_expression}")
#
#
# # 清理函数，确保在应用关闭时正确关闭调度器
# async def cleanup_scheduler():
#     if scheduler.running:
#         scheduler.shutdown()
#         logger.info("[定时任务] 调度器已关闭")
