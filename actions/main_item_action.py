from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from tools.main_agent import main_item_chatbot
import json
import re
from rasa_sdk.events import SlotSet
from tools.call_rasa import rasa_client
from tools.const import SELECTION
import logging


# 初始化日志记录器
logger = logging.getLogger(__name__)


class ActionMainItem(Action):

    def name(self) -> Text:
        return "action_main_item"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        input = tracker.latest_message.get("text")
        result = main_item_chatbot.chat(input)
        data = self.parse_response(result)
        msg = ""
        # print(data)
        logger.debug(f"from higent msg is {data}")
        if data['type'] == 'business_item':
            logger.debug(f"begin send msg to RASA")
            message = data['content']
            conversation_id = tracker.sender_id
            resp = rasa_client.send_message(
                sender_id=conversation_id, message=message)
            logger.debug(f"from rasa msg is {resp}")
            msg = resp[0]['text']
            dispatcher.utter_message(text=msg)
            if SELECTION in msg:
                return [SlotSet("follow_up", msg)]
            # if '查询完成,您需要准备以下材料' in msg:
            #     return [SlotSet("follow_up", None)]
        elif data['type'] == 'follow_up':
            logger.debug(f"begin return follow up")
            msg = data['content']
            dispatcher.utter_message(text=msg)
            return [SlotSet("follow_up", msg)]

    def parse_response(self, response_data):
        answer = response_data.get('answer', '')

        # 预定义模式
        biz_pattern = r'“业务主项”：(.*?)(，|$)'
        follow_up_pattern = r'“追问问题”：(.*?)(，|$)'

        # 提取业务主项
        biz_match = re.search(biz_pattern, answer)
        business_item = biz_match.group(1).strip() if biz_match else None

        # 提取追问问题
        follow_up_match = re.search(follow_up_pattern, answer)
        follow_up = follow_up_match.group(
            1).strip() if follow_up_match else None

        # 判断逻辑
        if business_item and business_item.lower() != '空':
            return {
                'type': 'business_item',
                'content': business_item
            }
        elif follow_up and follow_up.lower() != '空':
            return {
                'type': 'follow_up',
                'content': follow_up
            }
        else:
            return {
                'type': 'unknown',
                'content': answer
            }


# # 使用示例
# result = parse_response(response_data)
# print(result)
