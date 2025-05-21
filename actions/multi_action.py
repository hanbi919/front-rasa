from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from .sys_logger import logger
from .main_item_action import ActionMainItem
from .location_action import ActionLocation
from rasa_sdk.events import FollowupAction

class HandleMultipleIntents(Action):
    def name(self) -> Text:
        return "action_handle_multiple_intents"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # 获取识别出的意图
        intent = tracker.latest_message["intent"].get("name")

        if "+" in intent:
            # 分割多意图
            intents = intent.split("+")

            if "inform_main_item" in intents:
                logger.debug("inform_main_item")
                dispatcher.utter_message(text="你好！")

            if "provide_location" in intents:
                dispatcher.utter_message(text="今天天气晴朗，25摄氏度。")
                logger.debug("provide_location")

        # 先执行 ActionMainItem，然后执行 ActionLocation
        return [FollowupAction("action_provide_location"),FollowupAction("action_main_item"),
                ]
