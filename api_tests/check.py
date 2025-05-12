import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import jieba

# 设置jieba分词词典
jieba.setLogLevel('WARN')

# 自定义词典 - 添加公积金相关术语
finance_terms = [
    '公积金', '住房公积金', '贷款', '二手房', '新房', '借款人',
    '还款', '提前还款', '信息变更', '共同借款人', '还款账户'
]
for term in finance_terms:
    jieba.add_word(term)

# 读取Excel文件


def read_excel(file_path):
    df = pd.read_excel(file_path)
    return df

# 预处理文本


def preprocess_text(text):
    # 分词并去除停用词
    words = jieba.lcut(text)
    # 这里可以添加更多的停用词
    stopwords = ['的', '了', '用', '个', '是', '我', '你', '他', '这', '那']
    words = [word for word in words if word not in stopwords]
    return ' '.join(words)

# 计算语义相似度


def calculate_similarity(main_item, generalization):
    vectorizer = TfidfVectorizer(tokenizer=jieba.lcut)

    # 组合所有文本用于TF-IDF向量化
    all_texts = [main_item] + \
        [g for g in generalization.split('\n') if g.strip()]

    try:
        tfidf_matrix = vectorizer.fit_transform(all_texts)
    except ValueError:
        return []  # 如果无法向量化(如空文本)，返回空列表

    # 计算主项与每个泛化项的余弦相似度
    similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])

    # 返回相似度低于阈值的泛化项
    threshold = 0.3  # 相似度阈值，可根据实际情况调整
    low_sim_items = [gen for gen, sim in zip(generalization.split('\n'), similarities[0])
                     if sim < threshold and gen.strip()]

    return low_sim_items

# 主函数


def main():
    # 读取Excel文件
    file_path = 'api_tests/data/test.xlsx'
    df = read_excel(file_path)

    # 存储不符合的条目
    mismatches = {}

    for index, row in df.iterrows():
        main_item = row['一级事项名称']
        generalization = row['泛化']

        # 预处理主项文本
        processed_main = preprocess_text(main_item)

        # 计算并获取不符合的泛化项
        low_sim_items = calculate_similarity(processed_main, generalization)

        if low_sim_items:
            mismatches[main_item] = low_sim_items

    # 输出结果
    print("="*50)
    print("NLP语义校验结果 - 不符合的条目")
    print("="*50)

    for main_item, items in mismatches.items():
        print(f"\n一级事项名称: {main_item}")
        print("不符合的泛化项:")
        for item in items:
            print(f"- {item}")

    print("\n校验完成!")


if __name__ == "__main__":
    main()
