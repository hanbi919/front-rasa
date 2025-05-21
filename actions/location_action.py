from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from tools.district_agent import district_chatbot
from tools.call_rasa import rasa_client
from tools.const import SELECTION
from tools.decorators import log_execution_time
from .sys_logger import logger


class ActionLocation(Action):
    """处理位置信息查询的动作类"""

    def name(self) -> Text:
        """返回动作名称"""
        return "action_provide_location"

    @log_execution_time
    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        """
        执行位置信息查询的主要逻辑

        Args:
            dispatcher: 用于发送消息的调度器
            tracker: 当前对话追踪器
            domain: 对话域定义

        Returns:
            返回需要设置的事件列表
        """
        # 获取用户输入
        user_input = self._get_user_input(tracker)
        logger.debug(f"User input: {user_input}")
        # 与地区聊天机器人交互
        bot_response = self._query_district_chatbot(user_input)
        logger.debug(
            f"chatbot response is: {bot_response}")

        if "无地址信息" in bot_response:
            dispatcher.utter_message(response="utter_district_error")
            logger.warning(
                f"chatbot response is: {bot_response}")
            return []

        # 发送响应到Rasa并处理结果
        return self._process_rasa_response(
            dispatcher,
            tracker.sender_id,
            bot_response
        )

    def _get_user_input(self, tracker: Tracker) -> str:
        """从tracker中获取用户输入"""
        return tracker.latest_message.get("text")

    def _query_district_chatbot(self, user_input: str) -> Dict[Text, Any]:
        """查询地区聊天机器人并返回响应"""
        response = district_chatbot.chat(user_input)
        logger.debug(f"District chatbot response: {response}")
        return response

    def _process_rasa_response(
        self,
        dispatcher: CollectingDispatcher,
        conversation_id: str,
        bot_response: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        """
        处理Rasa的响应并返回适当的事件

        Args:
            dispatcher: 消息调度器
            conversation_id: 会话ID
            bot_response: 聊天机器人的响应

        Returns:
            需要设置的事件列表
        """
        # 发送到Rasa主服务
        area = bot_response['answer']
        rasa_response = rasa_client.send_message(
            sender_id=conversation_id,
            message=area
            # f'/all_area_intent{"area":"{area}"}'
        )
        # "message": "/all_district_intent{\"main_item\":\"辅助器具异地配置申请\"\\}"

        logger.debug(f"Response from RASA: {rasa_response}")

        # 获取响应消息并发送给用户
        response_message = rasa_response[0]['text']
        # 去掉 -
        if "-" in response_message:
            msg = msg.replace("-", " ")
        dispatcher.utter_message(text=response_message)

        # 根据响应内容决定返回的事件
        return self._build_response_events(response_message)

    def _build_response_events(self, message: str) -> List[Dict[Text, Any]]:
        """根据消息内容构建返回的事件列表"""
        if SELECTION in message:
            return [SlotSet("follow_up", message)]
        return []
