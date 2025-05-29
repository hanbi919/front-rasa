import ollama
from datetime import datetime

# 规则匹配函数（带时间打印）


def rule_based_response(user_input):
    start_time = datetime.now()
    user_input = user_input.lower()
    rules = {
        "办理材料": ["材料", "要啥材料", "需要什么材料", "带什么"],
        "办理地点": ["在哪儿办", "办理地址", "去哪里办", "地点"],
        "办理时间": ["办理时间", "啥时候能办", "几点上班", "工作时间"],
        "咨询方式": ["电话多少", "联系方式", "怎么联系", "咨询电话"],
        "是否收费": ["要钱吗", "收费吗", "多少钱", "是否收费"],
        "承诺办结时限": ["多久办完", "办结时限", "最快几天", "多长时间"],
        "受理条件": ["要啥条件", "符合什么条件", "受理条件", "资格"],
        "全部信息": ["所有信息", "全部内容", "完整流程", "概括一下"]
    }

    for response, keywords in rules.items():
        if any(keyword in user_input for keyword in keywords):
            end_time = datetime.now()
            print(
                f"[规则匹配] 耗时: {(end_time - start_time).total_seconds():.3f}s | 匹配回复: {response}")
            return response

    end_time = datetime.now()
    print(f"[规则未命中] 耗时: {(end_time - start_time).total_seconds():.3f}s")
    return None

# 调用 Ollama 模型（带时间打印）


def get_ollama_response(user_input):
    start_time = datetime.now()
    try:
        response = ollama.chat(
            model='deepseek-r1',
            messages=[{
                'role': 'user',
                'content': f'用户问：“{user_input}”。请直接返回用户输入的内容，不要添加任何解释。'
            }]
        )
        result = response['message']['content']
    except Exception as e:
        result = f"模型调用错误: {str(e)}"

    end_time = datetime.now()
    print(f"[模型调用] 耗时: {(end_time - start_time).total_seconds():.3f}s")
    return result

# 整合处理逻辑


def handle_user_query(user_input):
    print(f"\n[请求开始] 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"用户输入: {user_input}")

    # 先尝试规则匹配
    fixed_response = rule_based_response(user_input)
    if fixed_response:
        return fixed_response

    # 规则未命中时调用模型
    return get_ollama_response(user_input)


# 测试用例
test_queries = [
    "办理需要带什么材料？",
    "你们的办公地址在哪里？",
    "今天天气怎么样？"
]

for query in test_queries:
    response = handle_user_query(query)
    print(f"系统回复: {response}\n")
