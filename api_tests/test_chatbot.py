import pytest


def test_chatbot_response(chat_bot, api_test_data):
    """
    测试ChatBot对每个泛化查询返回的答案中包含对应的一级事项名称
    """
    primary_item, generalizations = api_test_data

    for query in generalizations:
        # 调用ChatBot API
        result = chat_bot.chat(query)

        # 验证响应
        assert 'answer' in result, "响应中缺少answer字段"
        assert 'duration' in result, "响应中缺少duration字段"

        # 验证返回的答案中包含一级事项名称
        assert primary_item in result['answer'], (
            f"查询: '{query}'\n"
            f"预期包含: '{primary_item}'\n"
            f"实际回答: '{result['answer']}'\n"
            f"响应时间: {result['duration']}秒"
        )
