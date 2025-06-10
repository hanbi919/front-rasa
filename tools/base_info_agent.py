# 区级政务中心地址和电话识别智能体

from .hiagent import ChatBot


class Base_Info_ChatBot(ChatBot):
    def __init__(self):
        # 第一个工具的配置参数
        super().__init__(
            api_key="d0tcn5gvfjfv26hr1qug",
            # api_key="d09c9r8a8cgtr0h4nqvg",
        )


# 可以在这里创建一个默认实例以便其他模块直接使用
# 用户选项识别机器人
# follow_up_chatbot = Follow_up_ChatBot()
