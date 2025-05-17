import streamlit as st
import time
import json
from datetime import datetime
from pathlib import Path
import re

# 页面设置
st.set_page_config(layout="wide")
st.title("📊 业务日志智能分析面板")

# 样式设置
st.markdown("""
<style>
.log-entry { 
    padding: 10px; 
    border-radius: 5px; 
    margin-bottom: 10px; 
    font-family: monospace;
}
.debug { background-color: #f0f0f0; }
.info { background-color: #e6f7ff; }
.warning { background-color: #fff7e6; }
.error { background-color: #ffebee; }
.user-input { font-weight: bold; color: #1e88e5; }
.bot-response { color: #43a047; }
.rasa-response { color: #6d4c41; }
.timestamp { color: #757575; font-size: 0.9em; }
.response-box { 
    background-color: #f8f9fa;
    padding: 10px;
    border-radius: 5px;
    margin-top: 5px;
    white-space: pre-wrap;
}
</style>
""", unsafe_allow_html=True)

LOG_FILE = "logs/application.log"


def parse_log_line(line):
    """解析单行日志"""
    try:
        # 示例日志格式：2025-05-17 22:08:49 - actions.sys_logger - DEBUG - User input: 住房公积金汇缴需要什么材料
        match = re.match(
            r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - (\S+) - (\S+) - (.*)$', line.strip())
        if not match:
            return None

        timestamp, logger_name, log_level, message = match.groups()

        return {
            "timestamp": timestamp,
            "logger": logger_name,
            "level": log_level,
            "message": message.strip()
        }
    except Exception as e:
        st.error(f"解析日志行出错: {e}")
        return None


def format_log_entry(log):
    """格式化日志条目"""
    if not log:
        return ""

    # 用户输入特殊处理
    if "user input:" in log["message"].lower():
        user_input = re.sub(r'user input:\s*', '',
                            log["message"], flags=re.IGNORECASE).strip()
        return f"""
        <div class="log-entry user-input">
            <span class="timestamp">{log["timestamp"]}</span> | 
            <strong>用户咨询</strong>: {user_input}
        </div>
        """

    # 机器人响应处理
    elif "chatbot is:" in log["message"].lower():
        chatbot_response = re.sub(
            r'chatbot is:\s*', '', log["message"], flags=re.IGNORECASE).strip()
        return f"""
        <div class="log-entry bot-response">
            <span class="timestamp">{log["timestamp"]}</span> | 
            <strong>业务分类</strong>: {chatbot_response}
        </div>
        """

    # RASA响应处理
    elif "from rasa msg is" in log["message"].lower():
        try:
            # 提取JSON部分
            json_str = log["message"].split("from rasa msg is")[1].strip()
            rasa_response = json.loads(json_str)

            if isinstance(rasa_response, list) and rasa_response:
                response_text = rasa_response[0].get('text', '')
                # 格式化带列表的响应
                formatted_text = response_text.replace(
                    '\n- ', '<br>- ').replace('\n', '<br>')

                return f"""
                <div class="log-entry rasa-response">
                    <span class="timestamp">{log["timestamp"]}</span> | 
                    <strong>系统回复</strong>:
                    <div class="response-box">{formatted_text}</div>
                </div>
                """
        except Exception as e:
            st.error(f"解析RASA响应出错: {e}")

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
            # 只关注actions.sys_logger的日志
            logs = [parse_log_line(line) for line in f.readlines()
                    if "actions.sys_logger" in line and parse_log_line(line)]
    except FileNotFoundError:
        st.error("日志文件不存在")
        return []
    except Exception as e:
        st.error(f"读取日志文件出错: {e}")
        return []

    return logs


def group_conversations(logs):
    """将日志按会话分组"""
    sessions = []
    current_session = []

    for log in reversed(logs):  # 从最新开始处理
        if log and ("user input:" in log["message"].lower()):
            if current_session:
                sessions.append(current_session)
            current_session = [log]
        elif log:
            current_session.append(log)

    if current_session:
        sessions.append(current_session)

    return sessions


# 主界面
st.sidebar.header("日志过滤选项")
refresh_rate = st.sidebar.slider("刷新频率(秒)", 1, 30, 5)
max_sessions = st.sidebar.slider("显示最近会话数", 1, 10, 5)

placeholder = st.empty()

while True:
    with placeholder.container():
        logs = display_logs()
        sessions = group_conversations(logs)

        if not sessions:
            st.warning("没有找到符合条件的日志")
        else:
            for i, session in enumerate(sessions[:max_sessions]):
                with st.expander(f"会话 {i+1} - {session[0]['timestamp']}", expanded=i == 0):
                    for log in session:
                        st.markdown(format_log_entry(log),
                                    unsafe_allow_html=True)

    time.sleep(refresh_rate)
