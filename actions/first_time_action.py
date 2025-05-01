from rasa_sdk import Action
from rasa_sdk.events import SessionStarted
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
class ActionCheckFirstInteraction(Action):
    def name(self) -> Text:
        return "action_check_first_interaction"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        history = tracker.events
        is_first_interaction = len(history) == 2 and isinstance(history[0], SessionStarted)

        if is_first_interaction:
            dispatcher.utter_message(text="欢迎首次来到我们的会话！")
            # 执行首次交互需要的其他逻辑
        else:
            dispatcher.utter_message(text="欢迎回来！")
            # 执行非首次交互需要的其他逻辑

        return []