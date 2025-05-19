import streamlit as st
import json
import re
import os
from datetime import datetime
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


def parse_timestamp(timestamp_str):
    """将时间戳字符串转换为datetime对象以便排序"""
    try:
        # 处理带毫秒的时间戳格式：2023-01-01 12:00:00,123
        if "," in timestamp_str:
            return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f")
        # 处理不带毫秒的时间戳格式
        return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
    except:
        return datetime.min  # 对于无效时间戳返回最早可能的时间

# 解析单条日志记录


def parse_log_entry(entry):
    try:
        log_data = json.loads(entry)
        # 确保每条日志都有timestamp字段
        if "timestamp" not in log_data:
            if "message" in log_data and isinstance(log_data["message"], str):
                match = re.match(
                    r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})', log_data["message"])
                if match:
                    log_data["timestamp"] = match.group(1)
        return log_data
    except json.JSONDecodeError:
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

    col1, col2 = st.columns([1, 4])

    with col1:
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
        message = entry.get("message", "")

        if isinstance(message, str) and ("{" in message or "[" in message):
            try:
                json_content = json.loads(message.replace("'", '"'))
                st.json(json_content)
                return
            except:
                pass

        st.text(message)

        for key, value in entry.items():
            if key not in ["timestamp", "level", "message"]:
                st.text(f"{key}: {value}")

# 读取日志文件内容


def read_log_file():
    if not os.path.exists(LOG_FILE):
        return []

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    log_entries = []
    current_entry = ""

    for line in content.split("\n"):
        if line.startswith("{") and current_entry:
            log_entries.append(current_entry.strip())
            current_entry = line
        else:
            current_entry += "\n" + line

    if current_entry:
        log_entries.append(current_entry.strip())

    return log_entries

# 按会话分组并排序


def group_and_sort_logs(log_entries):
    sessions = defaultdict(list)
    session_start_times = {}  # 记录每个会话的开始时间
    current_session_id = None
    session_count = 0

    # 解析所有日志条目并按时间排序
    parsed_entries = []
    for entry in log_entries:
        parsed = parse_log_entry(entry)
        if parsed:
            parsed_entries.append(parsed)

    # 按时间戳排序（从旧到新）
    parsed_entries.sort(key=lambda x: parse_timestamp(x.get("timestamp", "")))

    # 分组并记录会话开始时间
    for entry in parsed_entries:
        # 检测新会话开始
        if "User input" in str(entry.get("message", "")):
            session_count += 1
            current_session_id = f"会话-{session_count}"
            session_start_times[current_session_id] = parse_timestamp(
                entry.get("timestamp", ""))

        if current_session_id:
            sessions[current_session_id].append(entry)

    # 按会话开始时间排序（最新的在前）
    sorted_session_ids = sorted(session_start_times.keys(),
                                key=lambda x: session_start_times[x],
                                reverse=True)

    # 构建有序的会话字典
    ordered_sessions = {}
    for session_id in sorted_session_ids:
        # 每个会话内的日志按时间顺序排列（从旧到新）
        sessions[session_id].sort(
            key=lambda x: parse_timestamp(x.get("timestamp", "")))
        ordered_sessions[session_id] = sessions[session_id]

    return ordered_sessions

# 主程序逻辑


def main():
    if st.button('刷新日志'):
        st.rerun()

    col1, col2 = st.columns(2)

    with col1:
        level_filter = st.multiselect(
            "按日志级别筛选",
            options=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            default=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        )

    with col2:
        search_term = st.text_input("搜索关键词")

    log_entries = read_log_file()

    if not log_entries:
        st.warning("没有找到日志条目")
        return

    sessions = group_and_sort_logs(log_entries)

    st.sidebar.subheader("会话统计")
    st.sidebar.text(f"总会话数: {len(sessions)}")

    if os.path.exists(LOG_FILE):
        last_modified = os.path.getmtime(LOG_FILE)
        st.subheader(
            f"会话日志 (最后更新: {datetime.fromtimestamp(last_modified).strftime('%Y-%m-%d %H:%M:%S')})")
    else:
        st.subheader("会话日志")

    # 显示会话（最新的在前）
    for session_id, session_logs in sessions.items():
        with st.expander(f"{session_id} - 开始于: {session_logs[0].get('timestamp', '未知时间')} - 共{len(session_logs)}条日志"):
            for entry in session_logs:
                if entry.get("level", "INFO") in level_filter and \
                   (not search_term or search_term.lower() in str(entry).lower()):
                    display_log_entry(entry)


if __name__ == "__main__":
    if os.path.exists(LOG_FILE):
        main()
    else:
        st.error(f"日志文件 {LOG_FILE} 不存在，请确保文件路径正确")
