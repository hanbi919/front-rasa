from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis
import requests
from typing import Optional
import json
import hashlib
import time

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
REDIS_EXPIRE = 10  # Cache expiration time in seconds

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


def get_redis_connection():
    """Get Redis connection"""
    return redis.Redis(connection_pool=redis_pool)


def generate_cache_key(sender: str, message: str) -> str:
    """Generate cache key based on sender and message"""
    key_str = f"{sender}:{message}"
    return hashlib.sha256(key_str.encode()).hexdigest()

import re
# 方法1：使用正则表达式
def extract_user_message(input_str):
    # 匹配模式：用户问题："内容"，用户标识："ID"
    # 用户问题：“门诊慢特病待遇认定怎么办理”，用户标识：“asdiondk1lsjhuioqwejl112”
    pattern = r'用户问题：“(.+?)”，用户标识：“(.+?)”'
    match = re.search(pattern, input_str)

    if match:
        message = match.group(1)  # 门诊慢特病待遇认定怎么办理
        user = match.group(2)     # asdiondk1lsjhuioqwejl112
        return user, message
    else:
        return None, None


class ChatBot:
    def __init__(self,  host: str = "localhost", port: str = "5005"):

        self.host = host
        self.port = port

    def chat(self, sender, message) -> dict:
        """Interact with the Rasa webhook API"""

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
            response = requests.post(
                f"http://{self.host}:{self.port}/webhooks/rest/webhook",
                headers=headers,
                json=data,
                timeout=30.0
            )
            response.raise_for_status()

            # Rasa typically returns a list of messages
            responses = response.json()
            if isinstance(responses, list) and len(responses) > 0:
                result = responses[0].get('text', '')
            else:
                result = "No response from bot"

        except requests.exceptions.RequestException as e:
            raise HTTPException(
                status_code=500 if not hasattr(
                    e.response, 'status_code') else e.response.status_code,
                detail=f"Rasa API error: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Connection error: {str(e)}"
            )

        end_time = time.time()
        duration = "{:.2f}".format(end_time - start_time)

        return {
            "answer": result,
            "duration": duration
        }


@app.post("/chat", response_model=ChatResponse)
def chat_with_bot(request: ChatRequest):
    """Chat endpoint with caching functionality"""
    redis_conn = get_redis_connection()
    sender, message = extract_user_message(request.question)
    # Generate cache key based on sender and message
    cache_key = generate_cache_key(sender, message)

    # Try to get from cache
    cached_result = redis_conn.get(cache_key)
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
    try:
        bot = ChatBot()
        result = bot.chat(sender, message)

        # Store result in Redis
        cache_data = {
            "answer": result["answer"],
            "duration": result["duration"]
        }
        redis_conn.setex(cache_key, REDIS_EXPIRE, json.dumps(cache_data))

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
            message=str(e.detail)
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5678,
                limit_concurrency=1000,
                timeout_keep_alive=30)
