# 识别业务主项的智能体
from hiagent import ChatBot


class Check_ChatBot(ChatBot):
    def __init__(self):
        # 第一个工具的配置参数
        super().__init__(
            api_key="d0fn4ff292p9imkl90bg",
        )


# d0fn4ff292p9imkl90bg
# 可以在这里创建一个默认实例以便其他模块直接使用
check_chatbot = Check_ChatBot()
