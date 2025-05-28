from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection, utility
import pandas as pd
from sentence_transformers import SentenceTransformer
import hashlib

# 1. 连接到Milvus
connections.connect("default", host="localhost", port="19530")

# 2. 初始化文本嵌入模型
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')


def create_optimized_collection(collection_name):
    """创建针对主项名称和泛化字段优化的集合"""
    if utility.has_collection(collection_name):
        utility.drop_collection(collection_name)

    # 优化字段设计
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64,
                    is_primary=True, auto_id=True),
        FieldSchema(name="primary_name", dtype=DataType.VARCHAR,
                    max_length=500),  # 主项名称
        FieldSchema(name="generalization", dtype=DataType.VARCHAR,
                    max_length=2000),  # 泛化内容
        FieldSchema(name="combined_embedding",
                    dtype=DataType.FLOAT_VECTOR, dim=384),  # 组合嵌入
        FieldSchema(name="name_embedding",
                    dtype=DataType.FLOAT_VECTOR, dim=384),  # 单独名称嵌入
    ]

    schema = CollectionSchema(fields, description="主项名称和泛化内容专用集合")
    collection = Collection(collection_name, schema)

    # 为两个向量字段创建索引
    index_params = {
        "index_type": "IVF_FLAT",
        "metric_type": "L2",
        "params": {"nlist": 128}
    }
    collection.create_index("combined_embedding", index_params)
    collection.create_index("name_embedding", index_params)

    return collection


def process_excel_with_two_fields(file_path, collection_name="optimized_excel"):
    """处理包含主项名称和泛化字段的Excel文件"""
    # 读取Excel文件
    df = pd.read_excel(file_path)

    # 验证必要字段是否存在
    if not all(col in df.columns for col in ["主项名称", "泛化"]):
        raise ValueError("Excel文件必须包含'主项名称'和'泛化'两列")

    # 创建优化集合
    collection = create_optimized_collection(collection_name)

    # 准备批量插入数据
    batch_data = {
        "primary_name": [],
        "generalization": [],
        "combined_embedding": [],
        "name_embedding": []
    }

    # 处理每一行数据
    for _, row in df.iterrows():
        primary_name = str(row["主项名称"])
        generalization = str(row["泛化"])

        # 生成两种向量
        combined_text = f"主项:{primary_name}；泛化:{generalization}"
        combined_embedding = model.encode(combined_text)
        name_embedding = model.encode(primary_name)

        # 收集数据
        batch_data["primary_name"].append(primary_name)
        batch_data["generalization"].append(generalization)
        batch_data["combined_embedding"].append(combined_embedding.tolist())
        batch_data["name_embedding"].append(name_embedding.tolist())

    # 插入数据
    insert_result = collection.insert(batch_data)
    collection.load()

    print(f"成功上传 {len(insert_result.primary_keys)} 条记录")
    return collection


# 使用示例
if __name__ == "__main__":
    excel_file = "llm/result.xlsx"  # 替换为您的文件路径

    # 处理并上传文件
    collection = process_excel_with_two_fields(excel_file)

    # 双维度查询示例
    def hybrid_search(query_text, name_weight=0.3, content_weight=0.7, limit=5):
        query_embedding = model.encode(query_text)

        # 混合搜索参数
        search_params = {
            "anns_field": "combined_embedding",
            "param": {"metric_type": "L2", "params": {"nprobe": 16}},
            "limit": limit,
            "expr": None,
            "output_fields": ["primary_name", "generalization"]
        }

        # 执行搜索
        results = collection.search(
            data=[query_embedding.tolist()],
            **search_params
        )

        print(f"\n混合查询结果: '{query_text}'")
        for hits in results:
            for hit in hits:
                print(f"主项: {hit.entity.get('primary_name')}")
                print(f"泛化内容: {hit.entity.get('generalization')[:100]}...")
                print(f"相似度: {1 - hit.distance:.4f}\n")

    # 测试查询
    hybrid_search("提前还点公积金贷款咋办")
    hybrid_search("公积金二手房贷款如何办理", name_weight=0.5, content_weight=0.5)
