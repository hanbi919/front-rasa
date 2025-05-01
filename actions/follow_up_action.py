from typing import Any, Text, Dict, List
from rasa_sdk import Action
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, ActiveLoop
from rasa_sdk import Tracker
from tools.follow_up_agent import follow_up_chatbot
from tools.call_rasa import rasa_client
from tools.const import SELECTION
import logging
from tools.decorators import log_execution_time

# 初始化日志记录器
logger = logging.getLogger(__name__)


class ActionFollowUp(Action):
    """处理用户追问的回复动作"""

    def name(self) -> Text:
        """返回动作名称"""
        return "action_follow_up"

    @log_execution_time
    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        """执行追问处理逻辑"""
        # 获取对话信息
        user_answer = tracker.latest_message.get("text")
        answer = tracker.get_slot("answer")
        follow_up = tracker.get_slot("follow_up")

        # 构建追问格式字符串
        format_str = self._build_follow_up_format(follow_up, user_answer)

        # 与追问聊天机器人交互
        data = follow_up_chatbot.chat(format_str)
        logger.debug(f"From follow_up_chatbot: {data['answer']}")

        # 发送消息到Rasa并获取响应
        conversation_id = tracker.sender_id
        resp = self._send_to_rasa(conversation_id, data['answer'])
        logger.debug(f"From Rasa: {resp}")

        # 处理响应
        msg = resp[0]['text']
        dispatcher.utter_message(text=msg)

        # 根据响应内容返回不同的事件
        return self._build_response_events(msg)

    def _build_follow_up_format(self, follow_up: str, user_answer: str) -> str:
        """构建追问格式字符串"""
        return f"""
        追问问题:
        {follow_up}
        追问回复:
        {user_answer}
        """

    def _send_to_rasa(self, sender_id: str, message: str) -> Any:
        """发送消息到Rasa服务"""
        return rasa_client.send_message(
            sender_id=sender_id,
            message=message
        )

    def _build_response_events(self, message: str) -> List[Dict[Text, Any]]:
        """根据消息内容构建返回事件列表"""
        if SELECTION in message:
            return [
                SlotSet("follow_up", message),
                SlotSet("answer", None),
                ActiveLoop("follow_up_form")
            ]
        return []
