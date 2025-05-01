from typing import Any, Text, Dict, List
from tools.decorators import log_execution_time

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from tools.detail_agent import detail_chatbot
from tools.call_rasa import rasa_client
import logging
from rasa_sdk.events import SlotSet
from tools.const import SELECTION

# 初始化日志记录器
logger = logging.getLogger(__name__)


class ActionDetail(Action):

    def name(self) -> Text:
        return "action_detail"

    @log_execution_time
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # dispatcher.utter_message(text="欢迎使用智能客服系统")
        input = tracker.latest_message.get("text")
        result = detail_chatbot.chat(input)
        # data = self.parse_response(result)
        print(result['answer'])
        conversation_id = tracker.sender_id
        resp = rasa_client.send_message(
            sender_id=conversation_id, message=result['answer'])
        logger.debug(f"from rasa msg is {resp}")
        msg = resp[0]['text']
        dispatcher.utter_message(text=msg)
        if SELECTION in msg:
            return [SlotSet("follow_up", msg)]
        return []
