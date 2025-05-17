import logging
from logging.handlers import RotatingFileHandler
import os

# 创建logs目录(如果不存在)
os.makedirs('logs', exist_ok=True)

# 配置日志记录器


def setup_logger():
    # 创建logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # 设置日志级别

    # 创建文件处理器 - 每天轮换，保留7天
    file_handler = RotatingFileHandler(
        'logs/application.log',
        maxBytes=1024*1024*5,  # 5MB
        backupCount=7,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)

    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # 创建日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 将格式应用到处理器
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # 将处理器添加到logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


# 初始化日志配置
setup_logger()

# 获取模块特定的logger
logger = logging.getLogger(__name__)
