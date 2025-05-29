import requests
import json
import logging
from typing import Optional, List

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self, api_url: str, embedding_dim: int = 1024):
        self.api_url = api_url
        self.embedding_dim = embedding_dim
        self.headers = {'Content-Type': 'application/json'}

    def get_embedding(self, text: str) -> Optional[List[float]]:
        """获取文本向量"""
        if not text.strip():
            return None

        payload = {"inputs": text}

        try:
            response = requests.post(
                self.api_url,
                data=json.dumps(payload),
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            embedding = response.json()[0]

            if not isinstance(embedding, list) or len(embedding) != self.embedding_dim:
                logger.error(f"获取的嵌入向量维度不正确: {len(embedding)}")
                return None
            return embedding
        except Exception as e:
            logger.error(f"获取嵌入失败: {e}")
            return None
