from typing import Any, Text, Dict, List
from tools.decorators import log_execution_time

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from tools.detail_agent import detail_chatbot
from tools.call_rasa import rasa_client
from .sys_logger import logger
from rasa_sdk.events import SlotSet
from tools.const import SELECTION
from rasa_sdk.events import FollowupAction


class ActionDetail(Action):

    def name(self) -> Text:
        return "action_detail"

    @log_execution_time
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # dispatcher.utter_message(text="欢迎使用智能客服系统")
        input = tracker.latest_message.get("text")
        logger.info("收到用户输入", extra={
            "user_input": input,
            "intent": tracker.latest_message.get("intent", {}).get("name"),
            "entities": tracker.latest_message.get("entities", [])
        })

        result = detail_chatbot.chat(input)
        # data = self.parse_response(result)
        logger.debug("获取chatbot响应", extra={
            "response": result,
            "duration": result.get('duration', 'N/A')
        })
        conversation_id = tracker.sender_id
        resp = rasa_client.send_message(
            sender_id=conversation_id, message=result['answer'])
        # resp = rasa_client.send_message(
        # sender_id=conversation_id, message=input)
        logger.info("收到RASA响应", extra={
            "response": resp,
            "status": "success" if resp and resp[0]['text'] else "empty"
        })
        msg = resp[0]['text']

        if "未找到业务主项" in msg and len(input) > 10:
            return [FollowupAction("action_main_item")]

        if "0431-" in msg:
            msg = msg.replace("0431-", "0431 ")

        dispatcher.utter_message(text=msg)
        if SELECTION in msg:
            return [SlotSet("follow_up", msg)]
        return []
