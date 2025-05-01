import requests
import uuid
from typing import List, Dict, Optional


class RasaChatClient:
    """
    Rasa 聊天 API 客户端类
    功能：
    - 自动生成唯一的 sender_id (使用 UUID)
    - 封装消息发送和响应处理
    - 支持自定义服务器配置
    """

    def __init__(self, server_url: str = "http://116.141.0.116:5005"):
        """
        初始化 Rasa 客户端
        :param server_url: Rasa 服务器地址 (默认: http://localhost:5005)
        """
        self.server_url = server_url.rstrip('/')
        self.endpoint = "/webhooks/rest/webhook"
        self.default_headers = {"Content-Type": "application/json"}

    def _generate_sender_id(self) -> str:
        """生成基于 UUID 的唯一 sender_id"""
        return f"user_{uuid.uuid4().hex[:8]}"  # 取前8位缩短长度

    def send_message(
        self,
        message: str,
        sender_id: Optional[str] = None,
        timeout: float = 10.0
    ) -> List[Dict]:
        """
        发送消息到 Rasa 服务器并获取响应
        :param message: 要发送的文本消息
        :param sender_id: 可选的自定义用户ID (默认自动生成)
        :param timeout: 请求超时时间(秒)
        :return: Rasa 响应列表 (每个元素是包含 'text' 或自定义内容的字典)
        """
        payload = {
            "sender": sender_id if sender_id else self._generate_sender_id(),
            "message": message
        }

        try:
            url = f"{self.server_url}{self.endpoint}"
            response = requests.post(
                url,
                json=payload,
                headers=self.default_headers,
                timeout=timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[Rasa API 错误] 请求失败: {e}")
            return []

    @staticmethod
    def print_responses(responses: List[Dict]) -> None:
        """格式化打印 Rasa 响应"""
        if not responses:
            print("(无响应)")
            return

        for i, resp in enumerate(responses, 1):
            text = resp.get("text", "<无文本内容>")
            print(f"[响应 {i}] {text}")
            # 打印其他可能的字段（如图片、按钮等）
            for key in resp:
                if key != "text":
                    print(f"  - {key}: {resp[key]}")


# 使用示例
# if __name__ == "__main__":
    # 创建客户端实例
rasa_client = RasaChatClient()
# resp = rasa_client.send_message(
#      message="hi")
# msg = rasa_client.print_responses(resp)

