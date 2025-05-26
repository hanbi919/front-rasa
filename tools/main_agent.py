# 识别业务主项的智能体
from .hiagent import ChatBot


class Main_Item_ChatBot(ChatBot):
    def __init__(self):
        # 第一个工具的配置参数
        super().__init__(
            api_key="d090t37292p9imkl63j0",
        )

# 一级事项匹配机器人
# 可以在这里创建一个默认实例以便其他模块直接使用
# main_item_chatbot = Main_Item_ChatBot()
