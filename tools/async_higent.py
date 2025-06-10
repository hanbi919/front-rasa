import aiohttp
import asyncio
import json
import time
import redis.asyncio as redis
from typing import Dict, Any, Optional

# Redis configuration
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PASSWORD = None
REDIS_EXPIRE = 120  # Cache expiration time in seconds


class AsyncChatBot:
    def __init__(self, api_key: str, sender_id: str, redis_conn=None):
        '''
        初始化 AsyncChatBot 类的实例。
        参数：
        - api_key (str): API 密钥。
        - sender_id (str): 发送者唯一标识，用于Redis缓存
        - user_id (str): 用户ID，默认为"admin"
        '''
        self.user_id = "admin"
        self.api_key = api_key
        self.host = "116.141.0.87"
        self.port = "32300"
        self.session = None  # aiohttp 会话
        self.redis_client = redis_conn  # redis 客户端
        self.conversation_id = None  # 会在初始化时设置
        self.sender_id = sender_id  # 用于Redis缓存的key

    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession()
        # 初始化Redis连接
        if self.redis_client == None:
            self.redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                password=REDIS_PASSWORD,
                decode_responses=True  # 自动解码返回值为字符串
            )
        # 获取或创建 conversation_id
        self.conversation_id = await self.get_or_create_conversation()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.session.close()
        if self.redis_client:
            await self.redis_client.close()

    async def get_or_create_conversation(self) -> str:
        '''
        从Redis获取或创建新的对话ID。
        返回：
        str: 对话ID。
        '''
        # 尝试从Redis获取 conversation_id
        cached_id = await self.redis_client.get(f"conversation:{self.sender_id}")
        if cached_id:
            return cached_id

        # 如果没有缓存，创建新的对话
        new_id = await self.create_conversation()

        # 将新的 conversation_id 存入Redis
        await self.redis_client.setex(
            f"conversation:{self.sender_id}",
            REDIS_EXPIRE,
            new_id
        )

        return new_id

    async def create_conversation(self) -> str:
        '''
        异步创建一个新的对话。
        返回：
        str: 新创建的对话的 ID。
        '''
        url = f"http://{self.host}:{self.port}/api/proxy/api/v1/create_conversation"
        headers = {"Apikey": self.api_key, "Content-Type": "application/json"}
        data = {"Inputs": {"user_id": self.user_id}, "UserID": self.user_id}
        async with self.session.post(url, headers=headers, json=data) as response:
            response.raise_for_status()
            conversation = await response.json()
            return conversation['Conversation']['AppConversationID']

    async def chat(self, query: str) -> Dict[str, Any]:
        '''
        异步聊天方法
        参数：
        - query (str): 用户查询
        返回：
        Dict[str, Any]: 包含 answer 和 duration 的结果
        '''
        if not self.session:
            raise RuntimeError(
                "Session not initialized. Use async with or call init_session() first.")

        headers = {
            'Apikey': self.api_key,
            'Accept': 'text/event-stream',
            'Content-Type': 'application/json'
        }

        data = {
            'Query': query,
            'AppConversationID': self.conversation_id,
            'ResponseMode': 'streaming',
            'UserID': self.user_id,
        }

        result = ""
        start_time = time.time()

        try:
            async with self.session.post(
                f"http://{self.host}:{self.port}/api/proxy/api/v1/chat_query",
                headers=headers,
                json=data
            ) as response:
                if response.status == 200:
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line.startswith('data:data:'):
                            try:
                                json_data = json.loads(line[10:])
                                if json_data['event'] == "message":
                                    result += json_data['answer']
                            except json.JSONDecodeError as e:
                                print(f"JSON解析错误: {e}")
                                continue
                else:
                    print(f"请求失败: {response.status}, {response.reason}")
                    return {"answer": "", "duration": 0}
        except Exception as e:
            print(f"请求异常: {e}")
            return {"answer": "", "duration": 0}

        end_time = time.time()
        all_duration = end_time - start_time
        formatted_result = "{:.2f}".format(all_duration)
        return {"answer": result, "duration": formatted_result}


async def main():
    api_key = "d13qbg2f9ns5f38uuac0"
    sender_id = "user123"  # 使用唯一的sender_id

    # 使用异步上下文管理器
    async with AsyncChatBot(api_key, sender_id) as chat_bot:
        # 第一次聊天
        result1 = await chat_bot.chat("南关区服务中心地址是哪儿啊")
        print("第一次结果:", result1)

        # 第二次聊天（会使用缓存的conversation_id）
        result2 = await chat_bot.chat("电话多少")
        print("第二次结果:", result2)

if __name__ == "__main__":
    asyncio.run(main())
