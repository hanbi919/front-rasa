import requests
import json
import logging
from typing import Tuple, Optional

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QwenService:
    def __init__(self, api_url: str):
        self.api_url = api_url
        self.headers = {'Content-Type': 'application/json'}

    def call_qwen(self, query: str, context: str = "") -> Tuple[str, Optional[str]]:
        """调用Qwen模型生成响应"""
        messages = [
            {
                "role": "system",
                "content": """
                    # 技能
                    - 如果用户问题和知识库结果中的主项名称意思相近或内容完全一致，则输出: 主项名称 = 主项名称，追问问题 = 空
                    - 如果主项名称不完全相等或意思相近的主项名称有多条，生成追问问题，问题中详细列出主项名称有多少选项可以选择，让用户对可选项进行选择，增加序号输出，供用户选择。输出：主项名称 = 空，追问问题 = 追问的问题 
                    - 如果没有查询到信息，输出：主项名称 = 空，追问问题 = 空
                    # 约束
                    - 如果主项名称不为空，则追问问题必须为空，
                        例如：“业务主项”：律师事务所（分所）变更，“追问问题”：空
                    - 使用用户原本的输入查询知识库，不要总结上下文
                    - 完全依赖知识库的内容，不要自己发挥
                """
            },
            {
                "role": "user",
                "content": query
            }
        ]

        if context:
            messages.insert(1, {
                "role": "system",
                "content": f"知识库内容：{context}"
            })

        payload = {
            "model": "qwen",
            "messages": messages,
            "stream": False,
            "temperature": 0.5,
            "top_p": 0.5,
            "max_tokens": 16384
        }

        try:
            response = requests.post(
                self.api_url,
                data=json.dumps(payload),
                headers=self.headers,
                timeout=15
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"], None
        except Exception as e:
            logger.error(f"调用Qwen失败: {e}")
            return "", f"调用Qwen失败: {e}"
