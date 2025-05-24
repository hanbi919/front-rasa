from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, ActiveLoop
# from tools.async_main_agent import AsyncMainItemChatBot
from tools.main_agent import main_item_chatbot
from tools.call_rasa import rasa_client
from tools.const import SELECTION
from tools.decorators import log_execution_time
from .sys_logger import logger
import re
import asyncio

class ActionMainItem(Action):
    """处理业务主项和追问问题的动作类"""

    BUSINESS_ITEM_PATTERN = r'“业务主项”：(.*?)(?=，“|$)'
    FOLLOW_UP_PATTERN = r'“追问问题”：(.*?)(，|$)'

    def name(self) -> Text:
        return "action_main_item"

    @log_execution_time
    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        user_input = tracker.latest_message.get("text")
        logger.debug(f"User input: {user_input}")

        # Make synchronous call in a thread
        # async with AsyncMainItemChatBot() as chat_bot:
        #     chatbot_response = await chat_bot.chat(user_input)
        # chatbot_response = await asyncio.to_thread(main_item_chatbot.chat, user_input)
        chatbot_response = main_item_chatbot.chat(user_input)
        logger.debug(f"chatbot response is: {chatbot_response}")

        parsed_data = self.parse_response(chatbot_response)
        logger.debug(f"Parsed response from main_item_chatbot: {parsed_data}")

        if parsed_data['type'] == 'business_item':
            # Await the coroutine here
            return await self._handle_business_item(
                dispatcher,
                tracker.sender_id,
                tracker,
                parsed_data['content']
            )
        elif parsed_data['type'] == 'follow_up':
            # Await the coroutine here
            return await self._handle_follow_up(
                dispatcher,
                parsed_data['content']
            )
        elif parsed_data['type'] == 'unknown':
            # Await the coroutine here
            return await self._handle_unknown(dispatcher)

        return []

    def parse_response(self, response_data: Dict[Text, Any]) -> Dict[Text, Any]:
        answer = response_data.get('answer', '')
        business_item = self._extract_pattern(
            self.BUSINESS_ITEM_PATTERN, answer)
        follow_up = self._extract_pattern(self.FOLLOW_UP_PATTERN, answer)

        if business_item and business_item.lower() != '空':
            return {'type': 'business_item', 'content': business_item}
        elif follow_up and follow_up.lower() != '空':
            return {'type': 'follow_up', 'content': follow_up}
        return {'type': 'unknown', 'content': answer}

    def _extract_pattern(self, pattern: str, text: str) -> str:
        match = re.search(pattern, text)
        return match.group(1).strip() if match else None

    async def _handle_business_item(
        self,
        dispatcher: CollectingDispatcher,
        conversation_id: str,
        tracker: Tracker,
        message: str
    ) -> List[Dict[Text, Any]]:
        logger.debug(f"Sending business item to RASA: {message}")

        try:
            resp = await rasa_client.send_message_async(
                sender_id=conversation_id,
                message=message
            )
            logger.debug(f"Response from RASA: {resp}")

            if not resp or not isinstance(resp, list) or not resp[0].get('text'):
                dispatcher.utter_message(text="系统查询超时，请转人工服务")
                return []

            msg = resp[0]['text']
            dispatcher.utter_message(text=msg)

            if SELECTION in msg:
                follow_up = tracker.get_slot("follow_up")
                if follow_up is None:
                    return [
                        SlotSet("follow_up", msg),
                        ActiveLoop("follow_up_form")
                    ]
                else:
                    return [
                        SlotSet("follow_up", msg),
                        SlotSet("answer", None),
                        ActiveLoop("follow_up_form")
                    ]
            return []
        except Exception as e:
            logger.error(f"Error in _handle_business_item: {e}")
            dispatcher.utter_message(text="处理请求时发生错误")
            return []

    async def _handle_follow_up(
        self,
        dispatcher: CollectingDispatcher,
        message: str
    ) -> List[Dict[Text, Any]]:
        logger.debug(f"Handling follow up: {message}")
        dispatcher.utter_message(text=message)
        return [
            SlotSet("follow_up", message),
            ActiveLoop("follow_up_form")
        ]

    async def _handle_unknown(
        self,
        dispatcher: CollectingDispatcher,
    ) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(response="utter_main_item_unknown")
        return []
