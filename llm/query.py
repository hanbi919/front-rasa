from pymilvus import connections, Collection
import requests
import json
import logging
from typing import Optional, List, Dict, Any, Tuple

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 服务配置
MILVUS_HOST = "139.210.101.45"
MILVUS_PORT = "19999"
EMBED_API_URL = "http://139.210.101.45:12456/embed"
RERANK_API_URL = "http://139.210.101.45:12457/rerank"
QWEN_API_URL = "http://139.210.101.45:12455/v1/chat/completions"
HEADERS = {'Content-Type': 'application/json'}

# 向量维度（根据实际调整）
EMBEDDING_DIM = 1024
# 相似度阈值（COSINE相似度范围0-1，值越大越相似）
SIMILARITY_THRESHOLD = 0.5


def connect_to_milvus():
    """连接到Milvus"""
    try:
        connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)
        logger.info("成功连接到Milvus")
    except Exception as e:
        logger.error(f"连接Milvus失败: {e}")
        raise


def get_embedding(text: str) -> Optional[List[float]]:
    """获取文本向量"""
    if not text.strip():
        return None

    payload = {"inputs": text}

    try:
        response = requests.post(
            EMBED_API_URL,
            data=json.dumps(payload),
            headers=HEADERS,
            timeout=10
        )
        response.raise_for_status()
        embedding = response.json()[0]

        if not isinstance(embedding, list) or len(embedding) != EMBEDDING_DIM:
            logger.error(f"获取的嵌入向量维度不正确: {len(embedding)}")
            return None
        return embedding
    except Exception as e:
        logger.error(f"获取嵌入失败: {e}")
        return None


def rerank_results(query: str, texts: List[str]) -> Optional[List[Dict[str, Any]]]:
    """调用rerank API对结果重新排序"""
    if not texts:
        return None

    payload = {
        "query": query,
        "texts": texts
    }

    try:
        response = requests.post(
            RERANK_API_URL,
            data=json.dumps(payload),
            headers=HEADERS,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Rerank请求失败: {e}")
        return None


def call_qwen(query: str, context: str = "") -> Tuple[str, str]:
    """调用Qwen模型生成响应"""
    messages = [
        {
            "role": "system",
            "content": "你是一个规则引擎助手。根据以下规则回复用户：1. 如果用户输入包含'要啥条件'或'受理条件'，请固定回复：受理条件。2. 如果用户输入包含'所有信息'或'全部信息'，请固定回复：全部信息。 3. 否则，请原样返回用户的输入内容。"
        },
        {
            "role": "user",
            "content": query
        }
    ]

    if context:
        messages.insert(1, {
            "role": "system",
            "content": f"当前上下文信息：{context}"
        })

    payload = {
        "model": "qwen",
        "messages": messages,
        "stream": False,
        "temperature": 0.95,
        "top_p": 0.90,
        "max_tokens": 16384
    }

    try:
        response = requests.post(
            QWEN_API_URL,
            data=json.dumps(payload),
            headers=HEADERS,
            timeout=15
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"], ""
    except Exception as e:
        logger.error(f"调用Qwen失败: {e}")
        return "", f"调用Qwen失败: {e}"


def analyze_results(query: str, results: List[Any]) -> Tuple[str, str]:
    """
    分析搜索结果并生成响应
    :return: (main_service, follow_question)
    """
    if not results:
        return "", ""

    # 提取所有主项名称
    primary_names = list(set(
        hit.entity.get('primary_name', '')
        for hit in results
        if hit.entity.get('primary_name')
    ))

    # 如果只有一个主项名称，直接返回
    if len(primary_names) == 1:
        return primary_names[0], ""

    # 如果有多个主项名称，生成追问问题
    follow_up = f"找到多个相关服务，请选择您需要的服务：\n"
    for i, name in enumerate(primary_names, 1):
        follow_up += f"{i}. {name}\n"
    follow_up += "请输入对应数字选择服务。"

    return "", follow_up


def hybrid_search(collection_name: str, query_text: str, limit: int = 5):
    """
    执行混合搜索（带rerank和相似度过滤）
    :param collection_name: 集合名称
    :param query_text: 查询文本
    :param limit: 返回结果数量
    """
    try:
        # 获取集合
        collection = Collection(collection_name)
        collection.load()

        # 获取查询嵌入
        query_embedding = get_embedding(query_text)
        if query_embedding is None:
            raise ValueError("无法获取查询嵌入")

        # 搜索参数（使用COSINE相似度）
        search_params = {
            "anns_field": "combined_embedding",
            "param": {"metric_type": "COSINE", "params": {"nprobe": 16}},
            "limit": limit * 2,  # 初始多取一些结果用于过滤和rerank
            "output_fields": ["primary_name", "generalization"]
        }

        # 执行搜索
        results = collection.search(
            data=[query_embedding],
            **search_params
        )

        # 初步过滤结果（基于相似度）
        filtered_results = [
            hit for hit in results[0]
            if hit.distance >= SIMILARITY_THRESHOLD
        ]

        if not filtered_results:
            print("\n没有找到符合相似度阈值的结果")
            # 调用Qwen处理无结果情况
            qwen_response, _ = call_qwen(query_text)
            print(f"\nQwen回复: {qwen_response}")
            return {
                "mainService": "",
                "followQuestion": "",
                "qwenResponse": qwen_response
            }

        # 准备rerank数据
        texts_to_rerank = [
            f"{hit.entity.get('primary_name', '')}: {hit.entity.get('generalization', '')}"
            for hit in filtered_results
        ]

        # 调用rerank
        reranked = rerank_results(query_text, texts_to_rerank)

        if not reranked:
            print("\nRerank失败，使用原始排序结果")
            final_results = filtered_results[:limit]
        else:
            # 根据rerank结果重新排序
            reranked_indices = [item['index'] for item in reranked]
            final_results = [filtered_results[i]
                             for i in reranked_indices][:limit]

        # 分析结果并生成响应
        main_service, follow_question = analyze_results(
            query_text, final_results)

        # 调用Qwen处理用户原始问题
        qwen_response, qwen_error = call_qwen(query_text)
        if qwen_error:
            logger.error(qwen_error)

        # 构建最终响应
        response = {
            "mainService": main_service,
            "followQuestion": follow_question,
            "qwenResponse": qwen_response,
            "searchResults": [
                {
                    "id": hit.id,
                    "primaryName": hit.entity.get('primary_name'),
                    "generalization": hit.entity.get('generalization'),
                    "similarity": hit.distance
                }
                for hit in final_results
            ]
        }

        # 打印结果
        print(f"\n搜索查询: '{query_text}'")
        print(f"找到 {len(final_results)} 个符合条件的结果 (相似度>={SIMILARITY_THRESHOLD}):")

        if main_service:
            print(f"\n匹配的主项服务: {main_service}")
        if follow_question:
            print(f"\n追问问题: {follow_question}")

        print(f"\nQwen回复: {qwen_response}")

        return response

    except Exception as e:
        logger.error(f"搜索失败: {e}")
        return {
            "mainService": "",
            "followQuestion": "",
            "qwenResponse": f"系统错误: {str(e)}"
        }
    finally:
        collection.release()


if __name__ == "__main__":
    # 配置参数
    COLLECTION_NAME = "optimized_excel"
    QUERY_TEXT = "我想入职办理公积金"

    try:
        # 连接到Milvus
        connect_to_milvus()

        # 执行搜索
        result = hybrid_search(COLLECTION_NAME, QUERY_TEXT)

        # 你可以在这里使用result中的字段:
        # result["mainService"] - 匹配的主项服务
        # result["followQuestion"] - 需要追问的问题
        # result["qwenResponse"] - Qwen的回复
        # result["searchResults"] - 搜索结果列表

    except Exception as e:
        logger.error(f"程序执行失败: {e}")
    finally:
        # 断开连接
        connections.disconnect("default")
        logger.info("已断开与Milvus的连接")
