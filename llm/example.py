from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# 加载预训练模型
model = SentenceTransformer('all-MiniLM-L6-v2')

# 待比较的句子
sentences = [
    "如何提高编程技能？",
    "怎样提升代码水平？",
    "今天天气如何？"
]

# 生成句子嵌入向量
embeddings = model.encode(sentences)

# 计算相似度矩阵
similarity_matrix = cosine_similarity(embeddings)

# 输出结果
print("句子相似度矩阵：")
for i in range(len(sentences)):
    for j in range(i+1, len(sentences)):
        print(
            f"\"{sentences[i]}\" 和 \"{sentences[j]}\" 的相似度：{similarity_matrix[i][j]:.4f}")
