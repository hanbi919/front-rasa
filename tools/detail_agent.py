# 识别业务主项的智能体
from .hiagent import ChatBot


class Detail_ChatBot(ChatBot):
    def __init__(self):
        # 第一个工具的配置参数
        super().__init__(
            api_key="d091308a8cgtr0h4npng",
        )


# 可以在这里创建一个默认实例以便其他模块直接使用
detail_chatbot = Detail_ChatBot()
