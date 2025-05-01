from ..tools.main_agent import main_item_chatbot

import re


def parse_response(response_data):
    answer = response_data.get('answer', '')

    # 预定义模式
    biz_pattern = r'“业务主项”：(.*?)(，|$)'
    follow_up_pattern = r'“追问问题”：(.*?)(，|$)'

    # 提取业务主项
    biz_match = re.search(biz_pattern, answer)
    business_item = biz_match.group(1).strip() if biz_match else None

    # 提取追问问题
    follow_up_match = re.search(follow_up_pattern, answer)
    follow_up = follow_up_match.group(
        1).strip() if follow_up_match else None

    # 判断逻辑
    if business_item and business_item.lower() != '空':
        return {
            'type': 'business_item',
            'content': business_item
        }
    elif follow_up and follow_up.lower() != '空':
        return {
            'type': 'follow_up',
            'content': follow_up
        }
    else:
        return {
            'type': 'unknown',
            'content': answer
        }
    

result = main_item_chatbot.chat("我想办理伤残待遇申领业务，咋办啊")
resu=parse_response(result)
print(resu)
