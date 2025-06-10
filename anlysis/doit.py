import re
import pandas as pd
from collections import defaultdict

question_categories = {
    "办理时间": [
        r'时间', r'几点', r'何时', r'时候', r'工作日',
        r'周末', r'早上', r'下午', r'晚上', r'营业',
        r'几点到几点', r'什么时候.*(开门|上班|营业)',
        r'多久.*(办完|完成|处理好)',
        r'需要.*(天|小时)'
    ],
    "联系电话": [
        r'电话', r'号码', r'怎么联系', r'联系方式',
        r'打哪个', r'拨.*号', r'手机', r'座机',
        r'怎么.*找.*你们', r'怎么.*联系.*(人|你们)'
    ],
    "办理地点": [
        r'地点', r'地址', r'在哪', r'什么地方',
        r'哪个.*(地方|位置)', r'怎么.*去',
        r'在.*哪', r'位置', r'路线',
        r'几楼', r'哪个窗口', r'哪个部门'
    ]
}


def parse_conversation(text):
    """
    解析单条通话记录，提取客户咨询的业务
    """
    lines = text.split('\n')
    customer_lines = []

    for line in lines:
        if line.startswith('客户:'):
            # 去除"客户:"前缀和可能的话气词
            content = re.sub(r'^客户:[\s嗯啊噢]*', '', line).strip()
            if content:
                customer_lines.append(content)

    return customer_lines
def categorize_question(text):
    """
    分类用户提问内容
    """
    text = text.lower()  # 统一转为小写方便匹配

    for category, patterns in question_categories.items():
        for pattern in patterns:
            if re.search(pattern, text):
                return category
    return "其他问题"


def analyze_question_distribution(df, text_column='通话记录', manual_result_column='转人工结果'):
    """
    分析问题类型分布（过滤NaN值和转人工结果非空的记录）
    
    参数:
        df: 包含通话记录的DataFrame
        text_column: 存储通话记录的列名
        manual_result_column: 转人工结果字段的列名
        
    返回:
        包含统计结果的字典
    """
    # 初始化统计变量
    total_questions = 0
    category_counts = defaultdict(int)
    category_examples = defaultdict(list)

    # 过滤掉NaN值和转人工结果非空的记录
    df = df.dropna(subset=[text_column])

    # 如果存在转人工结果字段，过滤掉该字段不为空的记录
    if manual_result_column in df.columns:
        df = df[df[manual_result_column].isna()]  # 只保留转人工结果为空的记录

    for _, row in df.iterrows():
        conversation = row[text_column]

        # 确保conversation是字符串类型
        if not isinstance(conversation, str):
            continue

        customer_lines = parse_conversation(conversation)

        for line in customer_lines:
            # 跳过空行
            if not line.strip():
                continue

            total_questions += 1
            category = categorize_question(line)
            category_counts[category] += 1
            category_examples[category].append(line)

    # 计算百分比（防止除以零）
    results = []
    for category, count in category_counts.items():
        percentage = (count / total_questions) * \
            100 if total_questions > 0 else 0
        results.append({
            '问题类型': category,
            '出现次数': count,
            '占比(%)': round(percentage, 2),
            '示例': category_examples[category][0] if category_examples[category] else ''
        })

    # 按出现次数降序排序
    results.sort(key=lambda x: x['出现次数'], reverse=True)

    return {
        '总问题数': total_questions,
        '有效记录数': len(df),
        '分类统计': results,
        '目标问题占比(%)': round(
            sum(x['占比(%)']
                for x in results if x['问题类型'] in question_categories.keys()),
            2
        ) if total_questions > 0 else 0,
        '过滤说明': f"已过滤掉转人工结果非空的记录" if manual_result_column in df.columns else "未过滤转人工结果（无此字段）"
    }
# 加载数据
df = pd.read_excel('anlysis/通话记录.xlsx')

# 执行分析
results = analyze_question_distribution(df)

# 打印结果
print(f"总咨询问题数: {results['总问题数']}")
print(f"办理时间/电话/地点类问题总占比: {results['目标问题占比(%)']}%")

print("\n详细分类统计:")
for item in results['分类统计']:
    print(f"{item['问题类型']}: {item['占比(%)']}% (示例: '{item['示例'][:30]}...')")
