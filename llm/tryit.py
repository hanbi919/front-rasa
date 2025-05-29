from sentence_transformers import SentenceTransformer
from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection, utility

# Milvus 配置
MILVUS_HOST = "139.210.101.45"
MILVUS_PORT = "19999"
COLLECTION_NAME = "test_collection"

# 连接 Milvus
connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)

# 删除旧集合（可选）
if utility.has_collection(COLLECTION_NAME):
    utility.drop_collection(COLLECTION_NAME)

# 创建 schema
fields = [
    FieldSchema(name="id", dtype=DataType.INT64,
                is_primary=True, auto_id=False),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384)
]
schema = CollectionSchema(
    fields, description="Test collection for text embeddings")

# 创建集合
collection = Collection(name=COLLECTION_NAME, schema=schema)

# 文本转 embedding
model = SentenceTransformer("all-MiniLM-L6-v2")
texts = ["hello", "world", "milvus"]
embeddings = model.encode(texts)  # shape: (3, 384)
ids = [1, 2, 3]

# 插入数据
collection.insert([ids, embeddings.tolist()])
print("插入成功！")

# ⚠️ 创建索引（必须在插入数据后再创建）
index_params = {
    "metric_type": "L2",
    "index_type": "IVF_FLAT",
    "params": {"nlist": 1024}
}
collection.create_index(field_name="embedding", index_params=index_params)
print("索引创建成功！")

# 加载集合
collection.load()
print("集合加载成功！")
