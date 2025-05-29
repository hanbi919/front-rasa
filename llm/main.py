from embedding_service import EmbeddingService
from rerank_service import RerankService
from qwen_service import QwenService
from milvus_service import MilvusService
import logging
from typing import Dict, List, Any, Tuple
import pandas as pd

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HybridSearchApp:
    def __init__(self):
        # 初始化各服务
        self.embedding_service = EmbeddingService(
            api_url="http://139.210.101.45:12456/embed",
            embedding_dim=1024
        )
        self.rerank_service = RerankService(
            api_url="http://139.210.101.45:12457/rerank"
        )
        self.qwen_service = QwenService(
            api_url="http://139.210.101.45:12455/v1/chat/completions"
        )
        self.milvus_service = MilvusService(
            host="139.210.101.45",
            port="19999"
        )

        # 配置参数
        self.similarity_threshold = 0.5  # 相似度阈值
        self.default_limit = 5          # 默认返回结果数量
        self.rerank_enabled = True      # 是否启用rerank

    def analyze_results(self, query: str, results: List[Dict[str, Any]]) -> Tuple[str, str]:
        """
        分析搜索结果并生成响应
        :return: (main_service, follow_question)
        """
        if not results:
            return "", ""

        # 提取所有主项名称
        primary_names = list(set(
            result.get('primary_name', '')
            for result in results
            if result.get('primary_name')
        ))

        # 如果只有一个主项名称，直接返回
        if len(primary_names) == 1:
            return primary_names[0], ""

        # 如果有多个主项名称，生成追问问题
        follow_up = "找到多个相关服务，请选择您需要的服务：\n"
        follow_up += "\n".join(f"{i}. {name}" for i,
                               name in enumerate(primary_names, 1))
        follow_up += "\n请输入对应数字选择服务。"

        return "", follow_up

    def prepare_rerank_texts(self, results: List[Dict[str, Any]]) -> List[str]:
        """准备用于rerank的文本"""
        return [
            f"{res.get('primary_name', '')}"
            for res in results
        ]

    def process_search_results(
        self,
        query: str,
        initial_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        处理搜索结果：过滤、rerank等
        """
        # 初步过滤结果（基于相似度）
        filtered_results = [
            res for res in initial_results
            if res['distance'] >= self.similarity_threshold
        ]

        if not filtered_results or not self.rerank_enabled:
            return filtered_results[:self.default_limit]

        # 准备rerank数据
        texts_to_rerank = self.prepare_rerank_texts(filtered_results)

        # 调用rerank
        reranked = self.rerank_service.rerank_results(query, texts_to_rerank)

        if not reranked:
            logger.info("Rerank失败，使用原始排序结果")
            return filtered_results[:self.default_limit]

        # 根据rerank结果重新排序
        reranked_indices = [item['index'] for item in reranked]
        return [filtered_results[i] for i in reranked_indices][:self.default_limit]

    def hybrid_search(self, collection_name: str, query_text: str) -> Dict[str, Any]:
        """
        执行混合搜索完整流程
        :return: 包含mainService, followQuestion, qwenResponse和searchResults的字典
        """
        try:
            # 连接Milvus
            self.milvus_service.connect()

            # 获取查询嵌入
            query_embedding = self.embedding_service.get_embedding(query_text)
            if query_embedding is None:
                raise ValueError("无法获取查询嵌入")

            # 执行Milvus搜索（初始获取更多结果）
            initial_results = self.milvus_service.search(
                collection_name=collection_name,
                query_embedding=query_embedding,
                limit=self.default_limit * 2,
                similarity_threshold=0  # 先不过滤，后面统一处理
            )

            # 处理搜索结果
            final_results = self.process_search_results(
                query_text, initial_results)

            # 分析结果并生成响应
            main_service, follow_question = self.analyze_results(
                query_text, final_results)

            context = f"主项名称：{main_service}，追问问题：{follow_question}"

            # 调用Qwen处理用户原始问题
            qwen_response, qwen_error = self.qwen_service.call_qwen(
                query_text, context)
            if qwen_error:
                logger.error(qwen_error)

            # 构建最终响应
            return {
                "mainService": main_service,
                "followQuestion": follow_question,
                "qwenResponse": qwen_response,
                "searchResults": final_results
            }

        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return {
                "mainService": "",
                "followQuestion": "",
                "qwenResponse": f"系统错误: {str(e)}",
                "searchResults": []
            }
        finally:
            self.milvus_service.disconnect()

    def run(self, collection_name: str, query_text: str):
        """运行完整流程并打印结果"""
        result = self.hybrid_search(collection_name, query_text)

        # 打印结果
        print("\n=== 搜索结果 ===")
        print(f"查询: '{query_text}'")

        if result["mainService"]:
            print(f"\n匹配的主项服务: {result['mainService']}")
        if result["followQuestion"]:
            print(f"\n追问问题: {result['followQuestion']}")

        print(f"\nQwen回复: {result['qwenResponse']}")

        # print("\nMiluvs搜索结果详情:")
        # for idx, item in enumerate(result["searchResults"], 1):
        #     print(f"\n结果 #{idx}:")
        #     # print(f"ID: {item['id']}")
        #     print(f"主项: {item['primary_name']}")
        #     # print(f"泛化内容: {item['generalization'][:200]}...")
        #     print(f"相似度: {item['distance']:.4f}")

        return result


if __name__ == "__main__":
    # 示例测试
    app = HybridSearchApp()

    # 测试用例1 - 应匹配单个主项
    print("\n测试1: '公积金买二手房贷款'")
    app.run("optimized_excel", "公积金买二手房贷款")
    print("*"*20)

    # 测试用例2 - 可能匹配多个主项
    print("\n测试2: '请问一下建筑垃圾运输许可证怎么办理'")
    app.run("optimized_excel", "请问一下建筑垃圾运输许可证怎么办理")
    print("*"*20)

    # 测试用例3 - 无匹配结果
    print("\n测试3: '律师事务所要变更章程怎么办理'")
    app.run("optimized_excel", "律师事务所要变更章程怎么办理")
    print("*"*20)
# 测试用例3 - 无匹配结果
    print("\n测试4: '我想开个小食杂店，需要什么材料'")
    app.run("optimized_excel", "我想开个小食杂店，需要什么材料")
    print("*"*20)
    print("\n测试5: '信用卡咋办'")
    app.run("optimized_excel", "信用卡咋办")
    print("*"*20)
    print("\n测试5: '变更章程'")
    app.run("optimized_excel", "变更章程")

    # 变更章程
