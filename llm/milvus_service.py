from pymilvus import connections, Collection
import logging
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MilvusService:
    def __init__(self, host: str, port: str):
        self.host = host
        self.port = port
        self.connection = None

    def connect(self):
        """连接到Milvus数据库"""
        try:
            connections.connect("default", host=self.host, port=self.port)
            # 
            # COLLECTION_NAME = "optimized_excel"
            # collection = Collection(COLLECTION_NAME)
            # collection.load()
            # self.connection = collection
            # logger.info("成功连接到Milvus")
        except Exception as e:
            logger.error(f"连接Milvus失败: {e}")
            raise

    def disconnect(self):
        """断开Milvus连接"""
        if self.connection:
            connections.disconnect("default")
            logger.info("已断开与Milvus的连接")

    def search(
        self,
        collection_name: str,
        query_embedding: List[float],
        anns_field: str = "combined_embedding",
        metric_type: str = "COSINE",
        limit: int = 10,
        output_fields: List[str] = None,
        similarity_threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        执行向量搜索
        :return: 包含id、distance和实体字段的字典列表
        """
        if output_fields is None:
            output_fields = ["primary_name", "generalization"]

        try:
            collection = Collection(collection_name)
            collection.load()

            search_params = {
                "anns_field": anns_field,
                "param": {"metric_type": metric_type, "params": {"nprobe": 16}},
                "limit": limit,
                "output_fields": output_fields
            }

            results = collection.search(
                data=[query_embedding],
                **search_params
            )

            # 转换为字典列表并过滤
            formatted_results = []
            for hits in results:
                for hit in hits:
                    if hit.distance >= similarity_threshold:
                        formatted_results.append({
                            "id": hit.id,
                            "distance": hit.distance,
                            **{field: hit.entity.get(field) for field in output_fields}
                        })

            return formatted_results

        except Exception as e:
            logger.error(f"Milvus搜索失败: {e}")
            raise
        finally:
            if 'collection' in locals():
                collection.release()
