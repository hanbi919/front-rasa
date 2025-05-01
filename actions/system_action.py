from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from tools.main_agent import main_item_chatbot
import json
import re
from rasa_sdk.events import SlotSet
from tools.call_rasa import rasa_client
from rasa_sdk.events import Restarted
import logging
class ActionRestarted(Action):
    def name(self):
        return 'action_session_start'

    def run(self, dispatcher, tracker, domain):
        # 检查是否由 restart 触发
        if tracker.get_last_event_for("action") == "restart":
            return []

        # 正常的 session_start 逻辑
        conversation_id = tracker.sender_id
        resp = rasa_client.send_message(
            sender_id=conversation_id, message="/restart")
        dispatcher.utter_message(text="会话已初始化")

        return [Restarted()]
