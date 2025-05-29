from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection, utility
import pandas as pd
import requests
import json
import logging
from typing import Optional, List
from tqdm import tqdm

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Milvus连接配置
MILVUS_HOST = "139.210.101.45"
MILVUS_PORT = "19999"

# Embedding API配置
EMBED_API_URL = "http://139.210.101.45:12456/embed"
EMBEDDING_DIM = 1024  # 根据您的API实际输出维度调整
HEADERS = {'Content-Type': 'application/json'}

# 1. 连接到Milvus
try:
    connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)
    logger.info("成功连接到Milvus")
except Exception as e:
    logger.error(f"连接Milvus失败: {e}")
    raise


def get_embedding(text: str) -> Optional[List[float]]:
    """使用HTTP API获取文本向量"""
    if not text.strip():
        return None

    payload = {"inputs": text}

    try:
        response = requests.post(
            EMBED_API_URL,
            data=json.dumps(payload),
            headers=HEADERS,
            timeout=30  # 10秒超时
        )
        response.raise_for_status()
        embedding = response.json()[0]

        # 验证嵌入向量
        if not isinstance(embedding, list) or len(embedding) != EMBEDDING_DIM:
            logger.error(f"获取的嵌入向量维度不正确: {len(embedding)}")
            return None
        return embedding
    except requests.exceptions.RequestException as e:
        logger.error(f"获取嵌入失败: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"解析嵌入响应失败: {e}")
        return None


def create_optimized_collection(collection_name: str) -> Collection:
    """创建针对主项名称和泛化字段优化的集合"""
    try:
        if utility.has_collection(collection_name):
            logger.info(f"集合 {collection_name} 已存在，正在删除...")
            utility.drop_collection(collection_name)

        # 优化字段设计
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64,
                        is_primary=True, auto_id=True),
            FieldSchema(name="primary_name", dtype=DataType.VARCHAR,
                        max_length=500),
            FieldSchema(name="generalization", dtype=DataType.VARCHAR,
                        max_length=5000),
            FieldSchema(name="combined_embedding",
                        dtype=DataType.FLOAT_VECTOR, dim=EMBEDDING_DIM),
            # FieldSchema(name="name_embedding",
            #             dtype=DataType.FLOAT_VECTOR, dim=EMBEDDING_DIM),
        ]

        schema = CollectionSchema(fields, description="主项名称和泛化内容专用集合")
        collection = Collection(collection_name, schema)

        # 创建索引
        index_params = {
            "index_type": "IVF_FLAT",
            "metric_type": "COSINE",
            "params": {"nlist": 128}
        }

        logger.info("正在创建索引...")
        with tqdm(total=2, desc="创建索引进度") as pbar:
            collection.create_index("combined_embedding", index_params)
            pbar.update(1)
            # collection.create_index("name_embedding", index_params)  # 修复拼写错误
            # pbar.update(1)

        return collection

    except Exception as e:
        logger.error(f"创建集合失败: {e}")
        raise


def read_excel_data(file_path):
    df = pd.read_excel(file_path)
    data = []

    for _, row in df.iterrows():
        main_item = row['主项名称']
        generalizations = row['泛化'].split(
            '\n') if pd.notna(row['泛化']) else []

        # 为每个泛化项创建一条记录
        for gen in generalizations:
            if gen.strip():  # 跳过空字符串
                data.append({
                    '主项名称': main_item,
                    '泛化': gen.strip(),
                    '泛化合成': f"{main_item} {gen.strip()}"  # 合并文本用于向量化
                })

    return pd.DataFrame(data)


def read_excel_data_plus(file_path):
    df = pd.read_excel(file_path)
    data = []

    for _, row in df.iterrows():
        main_item = row['主项名称']
        gen = row['泛化']
        generalizations = row['泛化'].split(
            '\n') if pd.notna(row['泛化']) else []

        # 为每个泛化项创建一条记录
        row['泛化合成']=",".join(generalizations)
        # for gen in generalizations:
        #     if gen.strip():  # 跳过空字符串
        data.append({
            '主项名称': main_item,
            '泛化': gen.strip(),
            '泛化合成': f"主项名称:{main_item} 泛化:{gen.strip()}"  # 合并文本用于向量化
        })

    return pd.DataFrame(data)

def process_excel_with_two_fields(file_path: str, collection_name: str = "optimized_excel") -> Optional[Collection]:
    """处理包含主项名称和泛化字段的Excel文件，逐条插入数据"""
    try:
        logger.info(f"正在读取Excel文件: {file_path}")
        # df = pd.read_excel(file_path)
        df = read_excel_data_plus(file_path)
        # df = read_excel_data(file_path)

        # 验证必要字段
        # required_columns = ["主项名称", "泛化"]
        required_columns = ["主项名称", "泛化", '泛化合成']
        if not all(col in df.columns for col in required_columns):
            missing = [col for col in required_columns if col not in df.columns]
            raise ValueError(f"缺少必要列: {missing}")

        # 增强数据预处理
        def preprocess_text(text):
            if pd.isna(text):
                return ""
            if isinstance(text, list):
                return str(text[0]) if text else ""
            return str(text)

        df['主项名称'] = df['主项名称'].apply(preprocess_text)
        df['泛化'] = df['泛化'].apply(preprocess_text)

        # 创建集合
        collection = create_optimized_collection(collection_name)

        # 逐条处理数据
        logger.info("开始逐条处理数据...")
        success_count = 0
        failed_count = 0
        total_rows = len(df)

        with tqdm(total=total_rows, desc="数据处理进度") as pbar:
            for idx, row in df.iterrows():
                try:
                    primary_name = row["主项名称"].strip()
                    generalization = row["泛化"].strip()

                    if not primary_name:
                        logger.warning(f"第 {idx+1} 行主项名称为空，已跳过")
                        failed_count += 1
                        pbar.update(1)
                        continue


                    # 获取嵌入向量
                    # 为所有文本生成嵌入向量
                    # all_texts =  [row["主项名称"]] + [ row["泛化"].split("\n")]
                    # combined_text = f"{all_texts}"
                    combined_embedding = get_embedding(row['泛化合成'])
                    # name_embedding = get_embedding(primary_name)

                    if combined_embedding is None  :
                        logger.warning(f"第 {idx+1} 行获取嵌入失败，已跳过")
                        failed_count += 1
                        pbar.update(1)
                        continue

                    # 准备单条数据（注意：每个字段直接使用值，而非列表）
                    single_data = {
                        "primary_name": primary_name,  # 直接使用字符串
                        "generalization": generalization,  # 直接使用字符串
                        "combined_embedding": combined_embedding,  # 向量本身就是列表
                        # "name_embedding": name_embedding  # 向量本身就是列表
                    }

                    # 逐条插入
                    collection.insert([single_data])  # 注意：insert参数需要是列表包裹的字典
                    success_count += 1

                except Exception as e:
                    logger.error(f"处理第 {idx+1} 行数据时出错: {e}")
                    failed_count += 1
                finally:
                    pbar.update(1)

        logger.info(f"数据处理完成: 成功 {success_count} 条，失败 {failed_count} 条")
        return collection

    except Exception as e:
        logger.error(f"处理Excel文件失败: {e}")
        raise
def hybrid_search(collection: Collection, query_text: str, limit: int = 5):
    try:
        collection.load()
        query_embedding = get_embedding(query_text)

        if query_embedding is None:
            raise ValueError("无法获取查询嵌入")

        # 搜索参数
        search_params = {
            "anns_field": "combined_embedding",
            "param": {"metric_type": "COSINE", "params": {"nprobe": 16}},
            "limit": limit,
            "output_fields": ["primary_name", "generalization"]
        }

        results = collection.search(
            data=[query_embedding],
            **search_params
        )

        print(f"\n搜索查询: '{query_text}'")
        for hits in results:
            for hit in hits:
                print(f"ID: {hit.id}")
                print(f"主项: {hit.entity.get('primary_name')}")
                print(f"泛化内容: {hit.entity.get('generalization')[:100]}...")
                print(f"相似度: {hit.distance:.4f}\n")  # L2 距离越小越相似
    except Exception as e:
        logger.error(f"搜索失败: {e}")


if __name__ == "__main__":
    # excel_file = "llm/test.xlsx"  # 替换为您的文件路径
    excel_file = "llm/result.xlsx"  # 替换为您的文件路径

    try:
        # 处理并上传文件
        with tqdm(total=1, desc="整体处理进度") as pbar:
            collection = process_excel_with_two_fields(excel_file)
            pbar.update(1)

        if collection is None:
            raise RuntimeError("集合创建或数据处理失败")

        # 测试查询
        hybrid_search(collection, "提前还点公积金贷款")

    except Exception as e:
        logger.error(f"主程序执行失败: {e}")
    finally:
        connections.disconnect("default")
