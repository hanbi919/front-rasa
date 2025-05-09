from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis
import httpx
from typing import Optional
import json
import hashlib
import http.client
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应更严格
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Redis 配置
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PASSWORD = None  # 如果有密码请设置
REDIS_EXPIRE = 3600  # 缓存过期时间(秒)

# 初始化Redis连接池
redis_pool = redis.ConnectionPool(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD,
    decode_responses=True
)

# 请求模型


class NewConversationRequest(BaseModel):
    api_key: str    

class ChatRequest(BaseModel):
    conversation_id: str  # 现在使用 conversation_id 作为用户标识
    question: str
    api_key: str

# 响应模型


class ChatResponse(BaseModel):
    success: bool
    answer: str
    duration: str
    from_cache: bool
    conversation_id: str
    message: Optional[str] = None


def get_redis_connection():
    """获取Redis连接"""
    return redis.Redis(connection_pool=redis_pool)


def generate_cache_key(conversation_id: str, question: str) -> str:
    """生成缓存键，基于 conversation_id 和 question"""
    key_str = f"{conversation_id}:{question}"
    return hashlib.sha256(key_str.encode()).hexdigest()


class ChatBot:
    def __init__(self, api_key: str, conversation_id: Optional[str] = None,
                 host: str = "115.190.98.254", port: str = "80"):
        self.api_key = api_key
        self.host = host
        self.port = port
        self.conversation_id = conversation_id  # 使用传入的 conversation_id

    def create_conversation(self) -> str:
        """创建新对话"""
        url = f"http://{self.host}:{self.port}/api/proxy/api/v1/create_conversation"
        headers = {"Apikey": self.api_key, "Content-Type": "application/json"}
        data = {"Inputs": {"user_id": "admin123"},
                "UserID": "admin123"}  # 使用固定用户ID

        try:
            response = httpx.post(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            conversation = response.json()
            return conversation['Conversation']['AppConversationID']
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to create conversation: {str(e)}")

    def chat(self, query: str) -> dict:
        """与远程聊天API交互"""
        if not self.conversation_id:
            self.conversation_id = self.create_conversation()

        result = ""
        headers = {
            'Apikey': self.api_key,
            'Accept': 'text/event-stream',
            'Content-Type': 'application/json'
        }
        data = {
            'Query': query,
            'AppConversationID': self.conversation_id,
            'ResponseMode': 'streaming',
            'UserID': "admin123",  # 使用固定用户ID
        }

        start_time = time.time()
        try:
            connection = http.client.HTTPConnection(
                host=self.host, port=self.port)
            connection.request('POST', '/api/proxy/api/v1/chat_query',
                               body=json.dumps(data), headers=headers)
            response = connection.getresponse()

            if response.status == 200:
                for line in response:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data:data:'):
                        try:
                            json_data = json.loads(line[10:])
                            if json_data['event'] == "message":
                                result += json_data['answer']
                        except Exception:
                            continue
            else:
                raise HTTPException(
                    status_code=response.status,
                    detail=f"Remote API error: {response.reason}"
                )
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Connection error: {str(e)}")
        finally:
            connection.close()

        end_time = time.time()
        duration = "{:.2f}".format(end_time - start_time)

        return {
            "answer": result,
            "duration": duration,
            "conversation_id": self.conversation_id
        }


@app.post("/chat", response_model=ChatResponse)
async def chat_with_bot(request: ChatRequest):
    """聊天接口，带缓存功能"""
    redis_conn = get_redis_connection()

    # 初始化聊天机器人实例，使用传入的 conversation_id
    bot = ChatBot(api_key=request.api_key,
                  conversation_id=request.conversation_id)

    # 生成问题缓存键（基于 conversation_id 和 question）
    cache_key = generate_cache_key(
        bot.conversation_id or "new", request.question)

    # 尝试从缓存获取
    cached_result = redis_conn.get(cache_key)
    if cached_result is not None:
        cached_data = json.loads(cached_result)
        # 删除 Redis 中的 Key（确保数据已成功加载后再删除）
        # redis_conn.delete(cache_key)
        return ChatResponse(
            success=True,
            answer=cached_data["answer"],
            duration=cached_data["duration"],
            from_cache=True,
            conversation_id=bot.conversation_id or cached_data["conversation_id"],
            message="Result retrieved from cache"
        )

    # 缓存中没有，调用远程API
    try:
        result = bot.chat(request.question)

        # 将结果存入Redis
        cache_data = {
            "answer": result["answer"],
            "duration": result["duration"],
            "conversation_id": result["conversation_id"]
        }
        redis_conn.setex(cache_key, REDIS_EXPIRE, json.dumps(cache_data))

        return ChatResponse(
            success=True,
            answer=result["answer"],
            duration=result["duration"],
            from_cache=False,
            conversation_id=result["conversation_id"],
            message="Result retrieved from remote API and cached"
        )
    except HTTPException as e:
        return ChatResponse(
            success=False,
            answer="",
            duration="0.00",
            from_cache=False,
            conversation_id=bot.conversation_id or "",
            message=str(e.detail)
        )


@app.post("/new_conversation")
async def start_new_conversation(request: NewConversationRequest):
    """开始新的对话会话"""
    bot = ChatBot(api_key=request.api_key)

    try:
        # 创建新会话
        conversation_id = bot.create_conversation()

        return {
            "success": True,
            "conversation_id": conversation_id,
            "message": "New conversation started"
        }
    except HTTPException as e:
        return {
            "success": False,
            "conversation_id": "",
            "message": str(e.detail)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5678)
