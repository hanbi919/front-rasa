import re
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis.asyncio as redis
import aiohttp  # Changed to aiohttp
from typing import Optional
import json
import hashlib
import time
import asyncio

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis configuration
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PASSWORD = None
REDIS_EXPIRE = 20  # Cache expiration time in seconds

# Initialize Redis connection pool
redis_pool = redis.ConnectionPool(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD,
    decode_responses=True
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
    """Get Redis connection"""
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
    def __init__(self, host: str = "localhost", port: str = "5005"):
        self.host = host
        self.port = port
        self.excption = "服务器出现异常，请转人工服务。"
        self.timeout = "机器人响应超时，请您重新尝试。"
        self.session = aiohttp.ClientSession()  # Create a session on initialization

    async def close(self):
        """Close the aiohttp session"""
        await self.session.close()

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
        print(f"data is {data}")
        print(f"sender is {sender}")
        print(f"message is {message}")
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
            print(f"Client error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=self.excption
            )
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=self.excption
            )

        end_time = time.time()
        duration = "{:.2f}".format(end_time - start_time)

        return {
            "answer": result,
            "duration": duration
        }


@app.post("/chat", response_model=ChatResponse)
async def chat_with_bot(request: ChatRequest):
    """Chat endpoint with caching functionality"""
    redis_conn = await get_redis_connection()
    sender, message = extract_user_message(request.question)
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

    # If not in cache, call Rasa API
    bot = ChatBot()
    try:
        result = await bot.chat(sender, message)
        print(f"return data is {result}")

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
    finally:
        await bot.close()


@ app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    redis_conn=await get_redis_connection()
    await redis_conn.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5678,
                limit_concurrency=1000,
                timeout_keep_alive=30)
