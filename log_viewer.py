import streamlit as st
import json
import re
import os
import glob
from datetime import datetime
from collections import defaultdict

# 设置页面标题和布局
st.set_page_config(page_title="会话日志查看器", layout="wide")
st.title("会话日志查看程序")

# 日志文件路径配置（匹配RotatingFileHandler生成的模式）
LOG_DIR = "logs"
LOG_FILE_PATTERN = "application.log*"  # 匹配主日志和轮转日志

# 日志级别颜色映射
LEVEL_COLORS = {
    "DEBUG": "blue",
    "INFO": "green",
    "WARNING": "orange",
    "ERROR": "red",
    "CRITICAL": "purple"
}


def get_log_files():
    """获取所有日志文件并正确排序"""
    files = glob.glob(os.path.join(LOG_DIR, LOG_FILE_PATTERN))

    # 排序规则：
    # 1. 主日志文件(application.log)排在最前
    # 2. 轮转文件按编号升序排列(application.log.1, application.log.2等)
    def sort_key(f):
        basename = os.path.basename(f)
        if basename == "application.log":
            return (0, 0)
        parts = basename.split('.')
        if len(parts) == 3 and parts[-1].isdigit():
            return (1, int(parts[-1]))
        return (2, os.path.getmtime(f))

    return sorted(files, key=sort_key)


def parse_timestamp(timestamp_str):
    """将时间戳字符串转换为datetime对象"""
    try:
        # 处理带毫秒的时间戳格式：2023-01-01 12:00:00,123
        if "," in timestamp_str:
            return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f")
        # 处理不带毫秒的时间戳格式
        return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
    except:
        return datetime.min


def parse_log_entry(entry):
    """解析单条日志记录"""
    entry = entry.strip()
    if not entry:
        return None

    # 尝试解析为JSON
    try:
        log_data = json.loads(entry)
        # 确保有timestamp字段
        if "timestamp" not in log_data:
            if "message" in log_data and isinstance(log_data["message"], str):
                # 从message中提取时间戳
                match = re.match(
                    r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})',
                    log_data["message"]
                )
                if match:
                    log_data["timestamp"] = match.group(1)
        return log_data
    except json.JSONDecodeError:
        # 非JSON格式日志处理
        match = re.match(
            r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s+(\w+)\s+(.*)$',
            entry
        )
        if match:
            return {
                "timestamp": match.group(1),
                "level": match.group(2),
                "message": match.group(3)
            }
        return None


def display_log_entry(entry):
    """显示单条日志条目"""
    if not entry:
        return

    col1, col2 = st.columns([1, 4])

    with col1:
        timestamp = entry.get("timestamp", "")
        level = entry.get("level", "INFO").upper()

        if timestamp:
            st.text(timestamp)

        if level in LEVEL_COLORS:
            st.markdown(
                f"<span style='color:{LEVEL_COLORS[level]}'>[{level}]</span>",
                unsafe_allow_html=True
            )
        else:
            st.text(f"[{level}]")

    with col2:
        message = entry.get("message", "")
        extra_fields = {k: v for k, v in entry.items()
                        if k not in ["timestamp", "level", "message"]}

        # 尝试显示为JSON
        if isinstance(message, str) and any(c in message for c in "{["):
            try:
                json_content = json.loads(message)
                st.json(json_content)
            except:
                st.text(message)
        else:
            st.text(message)

        # 显示额外字段
        for key, value in extra_fields.items():
            st.text(
                f"{key}: {json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value}")


def read_all_logs():
    """读取并合并所有日志文件内容"""
    log_files = get_log_files()
    if not log_files:
        return []

    all_entries = []

    for log_file in log_files:
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    continue

                # 分割日志条目（处理多行JSON）
                entries = []
                buffer = []
                for line in content.split('\n'):
                    line = line.strip()
                    if not line:
                        continue

                    if line.startswith('{') and buffer:
                        entries.append('\n'.join(buffer))
                        buffer = [line]
                    else:
                        buffer.append(line)

                if buffer:
                    entries.append('\n'.join(buffer))

                all_entries.extend(entries)
        except Exception as e:
            st.warning(f"读取日志文件 {os.path.basename(log_file)} 时出错: {str(e)}")
            continue

    # 解析并排序所有条目
    parsed_entries = []
    for entry in all_entries:
        parsed = parse_log_entry(entry)
        if parsed:
            parsed_entries.append(parsed)

    # 按时间戳排序（从旧到新）
    parsed_entries.sort(key=lambda x: parse_timestamp(x.get("timestamp", "")))

    return parsed_entries


def group_and_sort_logs(log_entries):
    """按会话分组并排序日志"""
    sessions = defaultdict(list)
    session_start_times = {}
    current_session_id = None
    session_count = 0
    session_pattern = re.compile(
        r'(用户输入|User input|新会话|Session start)', re.IGNORECASE)

    for entry in log_entries:
        message = str(entry.get("message", ""))

        # 检测新会话开始
        if session_pattern.search(message):
            session_count += 1
            current_session_id = f"会话-{session_count}"
            session_start_times[current_session_id] = parse_timestamp(
                entry.get("timestamp", ""))

        if current_session_id:
            sessions[current_session_id].append(entry)

    # 按会话开始时间排序（最新的在前）
    sorted_sessions = sorted(
        sessions.items(),
        key=lambda x: session_start_times.get(x[0], datetime.min),
        reverse=True
    )

    return dict(sorted_sessions)


def main():
    """主界面"""
    st.sidebar.header("控制面板")
    if st.sidebar.button('🔄 刷新日志'):
        st.rerun()

    # 筛选条件
    col1, col2 = st.columns(2)
    with col1:
        level_filter = st.multiselect(
            "日志级别筛选",
            options=list(LEVEL_COLORS.keys()),
            default=list(LEVEL_COLORS.keys())
        )
    with col2:
        search_term = st.text_input("关键词搜索")

    # 读取日志
    log_entries = read_all_logs()
    if not log_entries:
        st.warning("没有找到日志条目")
        return

    # 分组会话
    sessions = group_and_sort_logs(log_entries)

    # 侧边栏统计信息
    log_files = get_log_files()
    st.sidebar.subheader("统计信息")
    st.sidebar.metric("日志文件数", len(log_files))
    st.sidebar.metric("总会话数", len(sessions))
    st.sidebar.metric("总日志条目", len(log_entries))

    with st.sidebar.expander("日志文件"):
        for file in log_files:
            st.caption(os.path.basename(file))

    # 主显示区域
    if log_files:
        last_modified = datetime.fromtimestamp(os.path.getmtime(log_files[0]))
        st.subheader(
            f"会话日志 (最后更新: {last_modified.strftime('%Y-%m-%d %H:%M:%S')})")
    else:
        st.subheader("会话日志")

    # 显示会话
    for session_id, session_logs in sessions.items():
        start_time = session_logs[0].get("timestamp", "未知时间")
        with st.expander(f"{session_id} - 开始于: {start_time} - 共{len(session_logs)}条日志"):
            for entry in session_logs:
                entry_level = entry.get("level", "INFO").upper()
                if (not level_filter or entry_level in level_filter) and \
                   (not search_term or search_term.lower() in str(entry).lower()):
                    display_log_entry(entry)


if __name__ == "__main__":
    if not os.path.exists(LOG_DIR):
        st.error(f"日志目录 {LOG_DIR} 不存在")
    else:
        main()
