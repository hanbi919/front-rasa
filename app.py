from fastapi.responses import StreamingResponse
import re
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis.asyncio as redis
import aiohttp
from typing import Optional
import json
import hashlib
import time
import asyncio
from tools.async_higent import AsyncChatBot
from tools.const import service_centers
from sys_logger import logger
# Redis configuration
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PASSWORD = None
REDIS_EXPIRE = 20  # Cache expiration time in seconds

# Global variables to hold shared resources
redis_pool = None
aiohttp_session = None
chat_bot = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan handler for managing shared resources"""
    global redis_pool, aiohttp_session, chat_bot

    # Initialize Redis connection pool
    redis_pool = redis.ConnectionPool(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD,
        decode_responses=True,
        max_connections=100
    )

    # Initialize aiohttp session
    aiohttp_session = aiohttp.ClientSession()
    chat_bot = ChatBot(aiohttp_session)

    yield  # Yield control to the application

    # Cleanup on shutdown
    if aiohttp_session:
        await aiohttp_session.close()
    if redis_pool:
        redis_conn = redis.Redis(connection_pool=redis_pool)
        await redis_conn.close()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models


class ChatRequest(BaseModel):
    question: str

# Response model


class ChatResponse(BaseModel):
    success: bool
    answer: str
    duration: str
    from_cache: bool
    message: Optional[str] = None


async def get_redis_connection():
    """Get Redis connection from the global pool"""
    return redis.Redis(connection_pool=redis_pool)


def generate_cache_key(sender: str, message: str) -> str:
    """Generate cache key based on sender and message"""
    key_str = f"{sender}:{message}"
    return hashlib.sha256(key_str.encode()).hexdigest()


def extract_user_message(input_str):
    # 匹配模式：用户问题："内容"，用户标识："ID"
    pattern = r'用户问题：“(.+?)”，用户标识：“(.+?)”'
    match = re.search(pattern, input_str)

    if match:
        message = match.group(1)
        user = match.group(2)
        return user, message
    else:
        return None, None


class ChatBot:
    def __init__(self, session: aiohttp.ClientSession, host: str = "localhost", port: str = "5005"):
        self.host = host
        self.port = port
        self.session = session  # Use the shared session
        self.exception = "服务器出现异常，请转人工服务。"
        self.timeout = "机器人响应超时，请您重新尝试。"
        self.data_error = "数据返回错误，请联系系统管理员。"

    async def chat(self, sender, message) -> dict:
        """Interact with the Rasa webhook API asynchronously"""
        result = ""
        headers = {
            'Content-Type': 'application/json',
        }
        data = {
            "sender": sender,
            "message": message
        }
        logger.info(f"data is {data}")
        logger.info(f"sender is {sender}")
        logger.info(f"message is {message}")
        start_time = time.time()

        try:
            async with self.session.post(
                f"http://{self.host}:{self.port}/webhooks/rest/webhook",
                headers=headers,
                json=data,
                timeout=aiohttp.ClientTimeout(total=30.0)
            ) as response:
                response.raise_for_status()

                # Rasa typically returns a list of messages
                responses = await response.json()
                if isinstance(responses, list) and len(responses) > 0:
                    result = responses[0].get('text', '')
                else:
                    result = self.timeout

        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=504,
                detail=self.timeout
            )
        except aiohttp.ClientError as e:
            logger.error(f"Client error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=self.exception
            )
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=self.exception
            )

        end_time = time.time()
        duration = "{:.2f}".format(end_time - start_time)

        return {
            "answer": result,
            "duration": duration
        }

# 直接和rasa前端交互


@app.post("/chat", response_model=ChatResponse)
async def chat_with_bot(request: ChatRequest):
    """Chat endpoint with caching functionality"""
    redis_conn = await get_redis_connection()
    sender, message = extract_user_message(request.question)

    if sender is None or message is None:
        return ChatResponse(
            success=False,
            answer="",
            duration="0.00",
            from_cache=False,
            message="Invalid message format"
        )

    # Generate cache key based on sender and message
    cache_key = generate_cache_key(sender, message)

    # Try to get from cache
    cached_result = await redis_conn.get(cache_key)
    if cached_result is not None:
        cached_data = json.loads(cached_result)
        return ChatResponse(
            success=True,
            answer=cached_data["answer"],
            duration=cached_data["duration"],
            from_cache=True,
            message="Result retrieved from cache"
        )

    # If not in cache, call Rasa API using the global ChatBot instance
    try:
        result = await chat_bot.chat(sender, message)
        logger.debug(f"return data is {result}")

        # Store result in Redis
        cache_data = {
            "answer": result["answer"],
            "duration": result["duration"]
        }
        await redis_conn.setex(cache_key, REDIS_EXPIRE, json.dumps(cache_data))

        return ChatResponse(
            success=True,
            answer=result["answer"],
            duration=result["duration"],
            from_cache=False,
            message="Result retrieved from Rasa API and cached"
        )
    except HTTPException as e:
        return ChatResponse(
            success=False,
            answer="",
            duration="0.00",
            from_cache=False,
            message=str(e.detail))

# 查询各个大厅的地址，电话，上班时间等


@app.post("/agent", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """Chat endpoint with caching functionality"""

    redis_conn = await get_redis_connection()
    sender, message = extract_user_message(request.question)

    if sender is None or message is None:
        return ChatResponse(
            success=False,
            answer="",
            duration="0.00",
            from_cache=False,
            message="Invalid message format"
        )

    # Generate cache key based on sender and message
    cache_key = generate_cache_key(sender, message)

    # Try to get from cache
    cached_result = await redis_conn.get(cache_key)
    if cached_result is not None:
        cached_data = json.loads(cached_result)
        return ChatResponse(
            success=True,
            answer=cached_data["answer"],
            duration=cached_data["duration"],
            from_cache=True,
            message="Result retrieved from cache"
        )

    # If not in cache, call Rasa API using the global ChatBot instance
    try:
        api_key = "d13qbg2f9ns5f38uuac0"

        # 使用异步上下文管理器
        area = ""
        async with AsyncChatBot(api_key, sender, redis_conn) as chat_bot:
            # 第一次聊天
            if "&" in sender:
                _area = sender.split("&")[-1]
                area = service_centers.get(_area, "")
            data = f"用户问题：“{message}”  用户地址：“{area}”"
            result = await chat_bot.chat(data)
        # result = await chat_bot.chat(sender, message)
        logger.debug(f"return data is {result}")
        # 去掉 -
        _answer = result["answer"]
        if "0431-" in _answer:
            _answer = _answer.replace("0431-", "0431 ")
        # Store result in Redis
        cache_data = {
            "answer": _answer,
            "duration": result["duration"]
        }
        await redis_conn.setex(cache_key, REDIS_EXPIRE, json.dumps(cache_data))

        return ChatResponse(
            success=True,
            answer=_answer,
            duration=result["duration"],
            from_cache=False,
            message="Result retrieved from Rasa API and cached"
        )
    except HTTPException as e:
        return ChatResponse(
            success=False,
            answer="",
            duration="0.00",
            from_cache=False,
            message=str(e.detail))


@app.post("/quick", response_model=ChatResponse)
async def chat_with_quick(request: ChatRequest):
    """Chat endpoint with caching functionality"""

    redis_conn = await get_redis_connection()
    sender, message = extract_user_message(request.question)

    if sender is None or message is None:
        return ChatResponse(
            success=False,
            answer="",
            duration="0.00",
            from_cache=False,
            message="Invalid message format"
        )

    # Generate cache key based on sender and message
    cache_key = generate_cache_key(sender, message)

    # Try to get from cache
    cached_result = await redis_conn.get(cache_key)
    if cached_result is not None:
        cached_data = json.loads(cached_result)
        return ChatResponse(
            success=True,
            answer=cached_data["answer"],
            duration=cached_data["duration"],
            from_cache=True,
            message="Result retrieved from cache"
        )

    # If not in cache, call Rasa API using the global ChatBot instance
    try:
        api_key = "d1j3m3hdi5hts8undi2g"
# d18cinpdi5hji2gj1o70
        # 使用异步上下文管理器
        area = ""
        async with AsyncChatBot(api_key, sender, redis_conn) as chat_bot:
            # 第一次聊天
            if "&" in sender:
                _area = sender.split("&")[-1]
                area = service_centers.get(_area, "")
            data = f"用户问题：“{message}”  用户地址：“{area}”"
            result = await chat_bot.chat(data)
        # result = await chat_bot.chat(sender, message)
        logger.debug(f"return data is {result}")
        # 去掉 -
        _answer = result["answer"]
        if "0431-" in _answer:
            _answer = _answer.replace("0431-", "0431,")
        # Store result in Redis
        cache_data = {
            "answer": _answer,
            "duration": result["duration"]
        }
        await redis_conn.setex(cache_key, REDIS_EXPIRE, json.dumps(cache_data))

        return ChatResponse(
            success=True,
            answer=_answer,
            duration=result["duration"],
            from_cache=False,
            message="Result retrieved from Rasa API and cached"
        )
    except HTTPException as e:
        return ChatResponse(
            success=False,
            answer="",
            duration="0.00",
            from_cache=False,
            message=str(e.detail))


def generate_sse_data():
    for i in range(5):
        time.sleep(1)
        yield f"data: Message {i}\n\n"


@app.get("/sse")
async def sse_stream():
    return StreamingResponse(generate_sse_data(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5678,
                limit_concurrency=1000,
                timeout_keep_alive=30)
