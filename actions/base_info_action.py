from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from tools.base_info_agent import Base_Info_ChatBot
from .sys_logger import logger
class BaseInfoWorld(Action):

    def name(self) -> Text:
        return "action_base_info"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        input = tracker.latest_message.get("text")
        logger.info("收到用户输入", extra={
            "user_input": input,
            "intent": tracker.latest_message.get("intent", {}).get("name"),
            "entities": tracker.latest_message.get("entities", [])
        })
        result = Base_Info_ChatBot().chat(input)
        logger.debug("获取chatbot响应", extra={
            "response": result,
            "duration": result.get('duration', 'N/A')
        })
        dispatcher.utter_message(text=result['answer'])
        return []
