# decorators.py
import logging
import time
from functools import wraps

# 配置日志（或者可以在主程序中配置）
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def log_execution_time(func):
    """记录函数执行时间的装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()

        if logger.isEnabledFor(logging.DEBUG):
            # 获取类名（如果方法是类方法）
            class_name = args[0].__class__.__name__ if args and hasattr(
                args[0], '__class__') else ''
            logger.debug(
                f"{class_name}.{func.__name__} 执行时间: {end_time - start_time:.6f}秒")

        return result
    return wrapper
