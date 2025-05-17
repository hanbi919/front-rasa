from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, ActiveLoop
from tools.main_agent import main_item_chatbot
from tools.call_rasa import rasa_client
from tools.const import SELECTION
from tools.decorators import log_execution_time
from .sys_logger import logger
import re
import json


class ActionMainItem(Action):
    """处理业务主项和追问问题的动作类"""

    # ... (保留原有代码不变)

    @log_execution_time
    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        user_input = tracker.latest_message.get("text")
        logger.info("收到用户输入", extra={
            "user_input": user_input,
            "intent": tracker.latest_message.get("intent", {}).get("name"),
            "entities": tracker.latest_message.get("entities", [])
        })

        try:
            chatbot_response = main_item_chatbot.chat(user_input)
            logger.debug("获取chatbot响应", extra={
                "response": chatbot_response,
                "duration": chatbot_response.get('duration', 'N/A')
            })

            parsed_data = self.parse_response(chatbot_response)
            logger.info("解析响应数据", extra={
                "type": parsed_data['type'],
                "content": parsed_data['content']
            })

            if parsed_data['type'] == 'business_item':
                return self._handle_business_item(
                    dispatcher,
                    tracker.sender_id,
                    tracker,
                    parsed_data['content']
                )
            elif parsed_data['type'] == 'follow_up':
                return self._handle_follow_up(
                    dispatcher,
                    parsed_data['content']
                )
            else:
                logger.warning("未知响应类型", extra={
                    "original_response": chatbot_response
                })
                return self._handle_unknown(dispatcher)

        except Exception as e:
            logger.error("处理请求时发生异常", exc_info=True)
            dispatcher.utter_message(text="系统处理出错，请稍后再试")
            return []

    def _handle_business_item(
        self,
        dispatcher: CollectingDispatcher,
        conversation_id: str,
        tracker,
        message: str
    ) -> List[Dict[Text, Any]]:
        logger.info("处理业务主项请求", extra={
            "business_item": message,
            "conversation_id": conversation_id
        })

        try:
            resp = rasa_client.send_message(
                sender_id=conversation_id,
                message=message
            )

            logger.info("收到RASA响应", extra={
                "response": resp,
                "status": "success" if resp and resp[0]['text'] else "empty"
            })

            msg = resp[0]['text']
            if not msg:
                logger.warning("RASA返回空响应")
                dispatcher.utter_message(text="系统查询超时，请转人工服务")
                return []

            dispatcher.utter_message(text=msg)

            if SELECTION in msg:
                follow_up = tracker.get_slot("follow_up")
                logger.debug("检测到需要追问的问题", extra={
                    "follow_up_question": msg,
                    "existing_follow_up": follow_up is not None
                })

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
            logger.error("处理业务主项时出错", exc_info=True)
            dispatcher.utter_message(text="处理业务请求时出错")
            return []
