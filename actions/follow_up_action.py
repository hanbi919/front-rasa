from rasa_sdk import Action
from rasa_sdk.events import SessionStarted
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from tools.follow_up_agent import follow_up_chatbot
from tools.call_rasa import rasa_client
from rasa_sdk.events import SlotSet
from tools.const import SELECTION

import logging


# 初始化日志记录器
logger = logging.getLogger(__name__)
# 处理用户追问的回复


class ActionFollowUp(Action):
    def name(self) -> Text:
        return "action_follow_up"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        user_answer = tracker.latest_message.get("text")
        follow_up = tracker.get_slot("follow_up")
        format_str = f"""
        追问问题:
        {follow_up}
        追问回复:
        {user_answer}
        """
        data = follow_up_chatbot.chat(format_str)
        # resp['answer']
        conversation_id = tracker.sender_id
        resp = rasa_client.send_message(
            sender_id=conversation_id, message=data['answer'])
        logger.debug(f"from rasa msg is {resp}")
        msg = resp[0]['text']
        dispatcher.utter_message(text=msg)
        if SELECTION in msg:
            return [SlotSet("follow_up", msg)]
        # else:
        #     return [SlotSet("follow_up", None)]
