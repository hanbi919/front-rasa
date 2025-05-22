import aiohttp
import asyncio
import json
import time
from typing import Dict, Any


class AsyncChatBot:
    def __init__(self, api_key: str):
        '''
        初始化 AsyncChatBot 类的实例。
        参数：
        - api_key (str): API 密钥。
        '''
        self.user_id = "admin123"
        self.api_key = api_key
        self.host = "115.190.98.254"
        self.port = "80"
        self.session = None  # aiohttp 会话
        self.conversation_id = None  # 会在初始化时设置

    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession()
        self.conversation_id = await self.create_conversation()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.session.close()

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
    api_key = "d091308a8cgtr0h4npng"

    # 使用异步上下文管理器
    async with AsyncChatBot(api_key) as chat_bot:
        # 第一次聊天
        result1 = await chat_bot.chat("我想办理残疾证业务，咋办啊")
        print("第一次结果:", result1)

        # 第二次聊天
        result2 = await chat_bot.chat("我想去哪里可以办呢")
        print("第二次结果:", result2)

if __name__ == "__main__":
    asyncio.run(main())
    """_summary_
    async with AsyncChatBot(api_key) as chat_bot:
    result = await chat_bot.chat("你的问题")
    """