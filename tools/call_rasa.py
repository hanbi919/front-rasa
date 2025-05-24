import aiohttp
import uuid
from typing import List, Dict, Optional


class RasaChatClient:
    """
    Rasa 聊天 API 客户端类 (异步版本)
    """

    _instance = None
    _session = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, server_url: str = "http://192.168.213.65:5005"):
        if not hasattr(self, '_initialized'):
            self.server_url = server_url.rstrip('/')
            self.endpoint = "/webhooks/rest/webhook"
            self.default_headers = {"Content-Type": "application/json"}
            self._initialized = True

    async def ensure_session(self):
        """Ensure we have a session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()

    def _generate_sender_id(self) -> str:
        """生成基于 UUID 的唯一 sender_id"""
        return f"user_{uuid.uuid4().hex[:8]}"

    async def send_message_async(
        self,
        message: str,
        sender_id: Optional[str] = None,
        timeout: float = 10.0
    ) -> List[Dict]:
        """
        异步发送消息到 Rasa 服务器
        """
        await self.ensure_session()

        payload = {
            "sender": sender_id if sender_id else self._generate_sender_id(),
            "message": message
        }
        headers = {
            **self.default_headers,
            "X-Sender-ID": payload["sender"]  # 添加 X-Sender-ID 头，值与 sender 相同
        }

        try:
            url = f"{self.server_url}{self.endpoint}"
            async with self._session.post(
                url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            print(f"[Rasa API 错误] 请求失败: {e}")
            return []

    # For synchronous contexts (not recommended in async code)
    def send_message(
        self,
        message: str,
        sender_id: Optional[str] = None,
        timeout: float = 10.0
    ) -> List[Dict]:
        """
        同步发送消息 (仅用于非异步环境)
        """
        import nest_asyncio
        nest_asyncio.apply()

        loop = asyncio.get_event_loop()
        return loop.run_until_complete(
            self.send_message_async(message, sender_id, timeout)
        )

    @staticmethod
    def print_responses(responses: List[Dict]) -> None:
        """格式化打印 Rasa 响应"""
        if not responses:
            print("(无响应)")
            return

        for i, resp in enumerate(responses, 1):
            text = resp.get("text", "<无文本内容>")
            print(f"[响应 {i}] {text}")
            for key in resp:
                if key != "text":
                    print(f"  - {key}: {resp[key]}")


# 全局实例
rasa_client = RasaChatClient()
