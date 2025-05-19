import streamlit as st
import json
import re
import time
from datetime import datetime
import os
from collections import defaultdict

# 设置页面标题和布局
st.set_page_config(page_title="会话日志查看器", layout="wide")
st.title("会话日志查看程序")

# 日志文件路径
LOG_FILE = "logs/application.log"

# 日志级别颜色映射
LEVEL_COLORS = {
    "DEBUG": "blue",
    "INFO": "green",
    "WARNING": "orange",
    "ERROR": "red",
    "CRITICAL": "purple"
}

# 解析单条日志记录


def parse_log_entry(entry):
    try:
        # 尝试解析为JSON
        return json.loads(entry)
    except json.JSONDecodeError:
        # 如果不是标准JSON，尝试解析为文本日志
        match = re.match(
            r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s+(\w+)\s+(.*)$', entry.strip())
        if match:
            return {
                "timestamp": match.group(1),
                "level": match.group(2),
                "message": match.group(3)
            }
        return None

# 显示日志条目


def display_log_entry(entry):
    if not entry:
        return

    # 创建列布局
    col1, col2 = st.columns([1, 4])

    with col1:
        # 显示时间戳和日志级别
        timestamp = entry.get("timestamp", "")
        level = entry.get("level", "INFO")

        if timestamp:
            st.text(timestamp)

        if level in LEVEL_COLORS:
            st.markdown(
                f"<span style='color:{LEVEL_COLORS[level]}'>[{level}]</span>", unsafe_allow_html=True)
        else:
            st.text(f"[{level}]")

    with col2:
        # 显示消息内容
        message = entry.get("message", "")

        # 尝试解析消息中的JSON
        if isinstance(message, str) and ("{" in message or "[" in message):
            try:
                json_content = json.loads(message.replace("'", '"'))
                st.json(json_content)
                return
            except:
                pass

        # 显示普通消息
        st.text(message)

        # 显示额外字段
        for key, value in entry.items():
            if key not in ["timestamp", "level", "message"]:
                st.text(f"{key}: {value}")

# 读取日志文件内容


def read_log_file():
    if not os.path.exists(LOG_FILE):
        return []

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # 分割日志条目
    log_entries = []
    current_entry = ""

    for line in content.split("\n"):
        # 检查是否是新日志条目的开始
        if line.startswith("{") and current_entry:
            log_entries.append(current_entry.strip())
            current_entry = line
        else:
            current_entry += "\n" + line

    if current_entry:
        log_entries.append(current_entry.strip())

    return log_entries

# 将日志分组为会话


def group_logs_by_session(log_entries):
    sessions = defaultdict(list)
    current_session_id = None
    session_count = 0

    for entry in log_entries:
        parsed = parse_log_entry(entry)
        if not parsed:
            continue

        # 检查是否是用户输入
        if "User input" in str(parsed.get("message", "")):
            session_count += 1
            current_session_id = f"会话-{session_count}"

        if current_session_id:
            sessions[current_session_id].append(parsed)

    return sessions

# 主程序逻辑


def main():
    # 添加筛选选项
    col1, col2 = st.columns(2)

    with col1:
        level_filter = st.multiselect(
            "按日志级别筛选",
            options=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            default=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        )

    with col2:
        search_term = st.text_input("搜索关键词")

    # 创建自动刷新区域
    refresh_placeholder = st.empty()

    # 上次文件修改时间
    last_modified = 0

    while True:
        # 检查文件是否被修改
        current_modified = os.path.getmtime(
            LOG_FILE) if os.path.exists(LOG_FILE) else 0

        if current_modified > last_modified:
            last_modified = current_modified

            # 读取日志文件
            log_entries = read_log_file()

            # 按会话分组
            sessions = group_logs_by_session(log_entries)

            # 显示会话列表
            with refresh_placeholder.container():
                st.subheader(
                    f"会话日志 (最后更新: {datetime.fromtimestamp(last_modified).strftime('%Y-%m-%d %H:%M:%S')})")

                # 显示会话统计
                st.sidebar.subheader("会话统计")
                st.sidebar.text(f"总会话数: {len(sessions)}")

                # 显示每个会话
                for session_id, session_logs in sessions.items():
                    with st.expander(f"{session_id} - 共{len(session_logs)}条日志"):
                        for entry in session_logs:
                            # 应用筛选
                            if entry.get("level", "INFO") in level_filter and \
                               (not search_term or search_term.lower() in str(entry).lower()):
                                display_log_entry(entry)

        # 等待10秒
        time.sleep(10)


if __name__ == "__main__":
    if os.path.exists(LOG_FILE):
        main()
    else:
        st.error(f"日志文件 {LOG_FILE} 不存在，请确保文件路径正确")
