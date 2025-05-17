import logging
from logging.handlers import RotatingFileHandler
import os
import json

# 创建logs目录(如果不存在)
os.makedirs('logs', exist_ok=True)


class JsonFormatter(logging.Formatter):
    def format(self, record):
        # 确保正确处理extra
        extra_data = {}
        if hasattr(record, 'extra'):
            extra_data = record.extra
        elif hasattr(record, '__dict__'):
            extra_data = {k: v for k, v in record.__dict__.items()
                          if k not in logging.LogRecord('', '', '', '', '', '', '').__dict__}

        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            **extra_data
        }
        return json.dumps(log_data, ensure_ascii=False, indent=2)


def setup_logger(name=__name__):
    """配置日志记录器"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # 清除现有处理器
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # 创建格式化器
    formatter = JsonFormatter()

    # 文件处理器
    file_handler = RotatingFileHandler(
        'logs/application.log',
        maxBytes=5*1024*1024,
        backupCount=7,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # 防止传播到父logger
    logger.propagate = False

    return logger


logger = setup_logger()
# 使用示例
if __name__ == "__main__":
    
    # 测试日志
    logger.debug("调试信息")
    logger.info("普通信息", extra={"user": "张三", "action": "登录"})
    logger.warning("警告信息", extra={"ip": "192.168.1.1", "status": 404})

    try:
        1/0
    except Exception as e:
        logger.error("发生错误", extra={
            "error": str(e),
            "context": {"user_id": 123, "page": "dashboard"}
        })
