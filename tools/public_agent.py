# 用户地址识别机器人

from .hiagent import ChatBot


class Public_ChatBot(ChatBot):
    def __init__(self):
        # 第一个工具的配置参数
        super().__init__(
            api_key="d1nmhu39oe2hubi97cog",
            # api_key="d09fdaf292p9imkl67c0",
        )

    def check_error(self, answer):
        if answer == "没有查到":
            return True
        else:
            return False


# 可以在这里创建一个默认实例以便其他模块直接使用
# 用户地址识别机器人
district_chatbot = Public_ChatBot()
