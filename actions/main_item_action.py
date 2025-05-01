from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, ActiveLoop
from tools.main_agent import main_item_chatbot
from tools.call_rasa import rasa_client
from tools.const import SELECTION
from tools.decorators import log_execution_time
import logging
import re

# 初始化日志记录器
logger = logging.getLogger(__name__)


class ActionMainItem(Action):
    """处理业务主项和追问问题的动作类"""

    # 正则表达式模式
    BUSINESS_ITEM_PATTERN = r'“业务主项”：(.*?)(，|$)'
    FOLLOW_UP_PATTERN = r'“追问问题”：(.*?)(，|$)'

    def name(self) -> Text:
        """返回动作名称"""
        return "action_main_item"

    @log_execution_time
    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        """
        执行主项处理逻辑

        Args:
            dispatcher: 消息调度器
            tracker: 对话追踪器
            domain: 对话域定义

        Returns:
            需要设置的事件列表
        """
        user_input = tracker.latest_message.get("text")
        chatbot_response = main_item_chatbot.chat(user_input)
        parsed_data = self.parse_response(chatbot_response)

        logger.debug(f"Parsed response from main_item_chatbot: {parsed_data}")

        if parsed_data['type'] == 'business_item':
            return self._handle_business_item(
                dispatcher,
                tracker.sender_id,
                parsed_data['content']
            )
        elif parsed_data['type'] == 'follow_up':
            return self._handle_follow_up(
                dispatcher,
                parsed_data['content']
            )
        elif parsed_data['type'] == 'unknown':
            return self._handle_unknown(
                dispatcher,
            )

        return []

    def parse_response(self, response_data: Dict[Text, Any]) -> Dict[Text, Any]:
        """
        解析聊天机器人的响应数据

        Args:
            response_data: 聊天机器人的原始响应

        Returns:
            解析后的数据结构:
            {
                'type': 'business_item'|'follow_up'|'unknown',
                'content': str
            }
        """
        answer = response_data.get('answer', '')

        business_item = self._extract_pattern(
            self.BUSINESS_ITEM_PATTERN, answer)
        follow_up = self._extract_pattern(self.FOLLOW_UP_PATTERN, answer)

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

        return {
            'type': 'unknown',
            'content': answer
        }

    def _extract_pattern(self, pattern: str, text: str) -> str:
        """辅助方法：从文本中提取正则匹配内容"""
        match = re.search(pattern, text)
        return match.group(1).strip() if match else None

    def _handle_business_item(
        self,
        dispatcher: CollectingDispatcher,
        conversation_id: str,
        message: str
    ) -> List[Dict[Text, Any]]:
        """处理业务主项类型的响应"""
        logger.debug(f"Sending business item to RASA: {message}")

        resp = rasa_client.send_message(
            sender_id=conversation_id,
            message=message
        )
        logger.debug(f"Response from RASA: {resp}")

        msg = resp[0]['text']
        if not msg:
            dispatcher.utter_message(text="系统查询超时，请转人工服务")
            return []

        dispatcher.utter_message(text=msg)

        if SELECTION in msg:
            return [
                SlotSet("follow_up", msg),
                ActiveLoop("follow_up_form")
            ]
        return []

    def _handle_follow_up(
        self,
        dispatcher: CollectingDispatcher,
        message: str
    ) -> List[Dict[Text, Any]]:
        """处理追问问题类型的响应"""
        logger.debug(f"Handling follow up: {message}")
        dispatcher.utter_message(text=message)
        return [
            SlotSet("follow_up", message),
            ActiveLoop("follow_up_form")
        ]

    def _handle_unknown(
        self,
        dispatcher: CollectingDispatcher,

    ) -> List[Dict[Text, Any]]:
        """处理追问问题类型的响应"""
        dispatcher.utter_message(response="utter_unknown")
        return []
