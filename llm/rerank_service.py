import requests
import json
import logging
from typing import Optional, List, Dict, Any

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RerankService:
    def __init__(self, api_url: str):
        self.api_url = api_url
        self.headers = {'Content-Type': 'application/json'}

    def rerank_results(self, query: str, texts: List[str]) -> Optional[List[Dict[str, Any]]]:
        """调用rerank API对结果重新排序"""
        if not texts:
            return None

        payload = {
            "query": query,
            "texts": texts
        }

        try:
            response = requests.post(
                self.api_url,
                data=json.dumps(payload),
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Rerank请求失败: {e}")
            return None
