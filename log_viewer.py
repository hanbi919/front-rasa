import streamlit as st
import time
import json
from datetime import datetime
from pathlib import Path

# 页面设置
st.set_page_config(layout="wide")
st.title("📊 业务日志智能分析面板")

# 样式设置
st.markdown("""
<style>
.log-entry { padding: 10px; border-radius: 5px; margin-bottom: 10px; }
.debug { background-color: #f0f0f0; }
.info { background-color: #e6f7ff; }
.warning { background-color: #fff7e6; }
.error { background-color: #ffebee; }
.user-input { font-weight: bold; color: #1e88e5; }
.bot-response { color: #43a047; }
.rasa-response { color: #6d4c41; }
.timestamp { color: #757575; font-size: 0.9em; }
</style>
""", unsafe_allow_html=True)

LOG_FILE = "logs/application.log"


def parse_log_line(line):
    """解析单行日志"""
    try:
        parts = line.split(" - ")
        if len(parts) < 4:
            return None

        timestamp = parts[0]
        logger_name = parts[1]
        log_level = parts[2]
        message = " - ".join(parts[3:])

        return {
            "timestamp": timestamp,
            "logger": logger_name,
            "level": log_level,
            "message": message.strip()
        }
    except:
        return None


def format_log_entry(log):
    """格式化日志条目"""
    if not log:
        return ""

    # 用户输入特殊处理
    if "User input:" in log["message"]:
        user_input = log["message"].split(
            "User input:")[1].strip().replace('\n', '<br>')
        return f"""
        <div class="log-entry user-input">
            <span class="timestamp">{log["timestamp"]}</span> | 
            用户咨询: <strong>{user_input}</strong>
        </div>
        """

    # 机器人响应处理
    elif "chatbot response is:" in log["message"]:
        try:
            response = json.loads(log["message"].split(
                "chatbot response is:")[1].strip())
            business_item = response.get('answer', '').split('"业务主项"：')[
                1].split('，')[0]
            duration = response.get('duration', 'N/A')
            return f"""
            <div class="log-entry bot-response">
                <span class="timestamp">{log["timestamp"]}</span> | 
                业务主项: <strong>{business_item}</strong> | 
                处理耗时: {duration}秒
            </div>
            """
        except:
            raw_response = log["message"].split("chatbot response is:")[
                1].strip().replace('\n', '<br>')
            return f"""
            <div class="log-entry bot-response">
                <span class="timestamp">{log["timestamp"]}</span> | 
                机器人响应: {raw_response}
            </div>
            """

    # RASA响应处理
    elif "Response from RASA:" in log["message"] or "from rasa msg is" in log["message"]:
        try:
            rasa_response = eval(log["message"].split(":")[1].strip())
            if isinstance(rasa_response, list) and rasa_response:
                formatted_text = rasa_response[0].get(
                    'text', '').replace('\n', '<br>')
                return f"""
                <div class="log-entry rasa-response">
                    <span class="timestamp">{log["timestamp"]}</span> | 
                    系统回复: {formatted_text}
                </div>
                """
        except:
            pass

    # 默认格式
    message = log["message"].replace('\n', '<br>')
    return f"""
    <div class="log-entry {log["level"].lower()}">
        <span class="timestamp">{log["timestamp"]}</span> | 
        {message}
    </div>
    """

def display_logs():
    """读取并显示日志"""
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            logs = [parse_log_line(line) for line in f.readlines(
            ) if "actions.sys_logger" in line]
    except FileNotFoundError:
        st.error("日志文件不存在")
        return

    # 会话分组
    sessions = []
    current_session = []

    for log in reversed(logs):  # 从最新开始
        if log and "User input:" in log["message"]:
            if current_session:
                sessions.append(current_session)
            current_session = [log]
        elif log:
            current_session.append(log)

    if current_session:
        sessions.append(current_session)

    # 显示最近的5个会话
    for i, session in enumerate(sessions[:5]):
        with st.expander(f"会话 {i+1} - {session[0]['timestamp']}", expanded=i == 0):
            for log in reversed(session):
                st.markdown(format_log_entry(log), unsafe_allow_html=True)


# 主循环
placeholder = st.empty()
while True:
    with placeholder.container():
        display_logs()
    time.sleep(5)  # 每5秒刷新一次
