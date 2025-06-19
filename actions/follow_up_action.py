from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, ActiveLoop
from tools.follow_up_agent import Follow_up_ChatBot
from tools.call_rasa import rasa_client
from tools.const import SELECTION
from .sys_logger import logger
from tools.decorators import log_execution_time


class ActionFollowUp(Action):
    """处理用户追问的回复动作"""

    def name(self) -> Text:
        """返回动作名称"""
        return "action_follow_up"

    @log_execution_time
    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        """执行追问处理逻辑"""
        try:
            # 获取对话信息
            user_answer = tracker.latest_message.get("text")
            answer = tracker.get_slot("answer")
            follow_up = tracker.get_slot("follow_up")
            if not follow_up:
                logger.warning("follow up is None")
                dispatcher.utter_message(text="请说出您想要办理的业务")
                return []
            logger.info("开始处理追问请求", extra={
                "user_answer": user_answer,
                "previous_answer": answer,
                "follow_up_question": follow_up,
                "intent": tracker.latest_message.get("intent", {}).get("name"),
                "entities": tracker.latest_message.get("entities", [])
            })

            # 构建追问格式字符串
            format_str = self._build_follow_up_format(follow_up, user_answer)
            logger.debug("构建的追问格式字符串", extra={
                "formatted_string": format_str
            })

            # 与追问聊天机器人交互
            data = Follow_up_ChatBot().chat(format_str)
            logger.info("收到追问机器人响应", extra={
                "response": data,
                "duration": data.get('duration', 'N/A')
            })

            if "无法识别" in data['answer']:
                logger.warning("追问无匹配选项")
                dispatcher.utter_message(response="utter_follow_up_no_match")
                return []

            # 发送消息到Rasa并获取响应
            conversation_id = tracker.sender_id
            resp = await self._send_to_rasa(conversation_id, data['answer'])
            logger.info("收到RASA响应", extra={
                "response": resp,
                "status": "success" if resp and resp[0]['text'] else "empty"
            })

            if not resp or not resp[0]['text']:
                logger.error("RASA返回空响应")
                dispatcher.utter_message(text="系统查询超时，请转人工服务")
                return []

            # 处理响应
            msg = resp[0]['text']
            dispatcher.utter_message(text=msg)

            # 根据响应内容返回不同的事件
            events = self._build_response_events(msg)
            logger.debug("生成的事件列表", extra={
                "events": events
            })

            return events

        except Exception as e:
            logger.error("处理追问请求时发生异常", exc_info=True)
            dispatcher.utter_message(text="处理追问时出错，请稍后再试")
            return []

    def _build_follow_up_format(self, follow_up: str, user_answer: str) -> str:
        """构建追问格式字符串"""
        return f"""
        追问问题:
        {follow_up}
        追问回复:
        {user_answer}
        """

    async def _send_to_rasa(self, sender_id: str, message: str) -> Any:
        """发送消息到Rasa服务"""
        try:
            return await rasa_client.send_message_async(
                sender_id=sender_id,
                message=message
            )
        except Exception as e:
            logger.error("调用RASA服务失败", exc_info=True)
            raise

    def _build_response_events(self, message: str) -> List[Dict[Text, Any]]:
        """根据消息内容构建返回事件列表"""
        if SELECTION in message or "想查询哪方面" in message:
            logger.info("检测到需要进一步追问")
            return [
                SlotSet("follow_up", message),
                SlotSet("answer", None),
                ActiveLoop("follow_up_form")
            ]
        return []
