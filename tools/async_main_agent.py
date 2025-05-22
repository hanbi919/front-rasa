from .hiagent import AsyncChatBot  # 注意这里要导入异步版本


class AsyncMainItemChatBot(AsyncChatBot):
    def __init__(self):
        # 使用异步版本的父类初始化
        super().__init__(
            api_key="d090t37292p9imkl63j0"
        )

# 创建异步实例


# async def create_main_item_chatbot():
#     chatbot = AsyncMainItemChatBot()
#     await chatbot.__aenter__()  # 显式初始化会话
#     return chatbot

# 注意：不能在模块级别直接创建实例，因为需要异步上下文
# 使用时应该在异步函数中创建：
# async def some_function():
#     main_item_chatbot = await create_main_item_chatbot()
#     result = await main_item_chatbot.chat("问题")
#     await main_item_chatbot.__aexit__(None, None, None)  # 关闭会话
