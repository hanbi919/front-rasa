import threading
from queue import Queue
from contextlib import contextmanager
from .hiagent import ChatBot
from .main_agent import Main_Item_ChatBot

class Main_Item_ChatBot_Pool:
    def __init__(self, pool_size=20):
        # 线程安全队列存储实例
        self._pool = Queue(maxsize=pool_size)
        self._lock = threading.Lock()
        self._created_instances = 0
        self.max_size = pool_size

        # 预初始化连接池
        self._initialize_pool()

    def _initialize_pool(self):
        """预创建实例到池中"""
        for _ in range(min(5, self.max_size)):  # 预热5个实例
            self._pool.put(self._create_instance())

    def _create_instance(self):
        """创建新实例（带异常处理）"""
        with self._lock:
            if self._created_instances >= self.max_size:
                raise RuntimeError("Maximum pool size reached")

            try:
                instance = Main_Item_ChatBot()
                self._created_instances += 1
                return instance
            except Exception as e:
                raise RuntimeError(f"Instance creation failed: {str(e)}")

    @contextmanager
    def get_instance(self, timeout=10):
        """获取实例的上下文管理器"""
        instance = None
        try:
            # 优先从队列获取，队列为空则新建（不超过max_size）
            try:
                instance = self._pool.get(timeout=timeout)
            except Queue.Empty:
                if self._created_instances < self.max_size:
                    instance = self._create_instance()
                else:
                    raise TimeoutError("No available instances in pool")

            yield instance

        finally:
            # 确保实例归还
            if instance is not None:
                self._pool.put(instance)

    def current_stats(self):
        """返回资源池状态"""
        with self._lock:
            return {
                "available": self._pool.qsize(),
                "created": self._created_instances,
                "max_size": self.max_size
            }


# 全局资源池（单例模式）
_main_item_pool = None
_pool_lock = threading.Lock()


def get_global_pool(pool_size=20):
    global _main_item_pool
    if _main_item_pool is None:
        with _pool_lock:
            if _main_item_pool is None:
                _main_item_pool = Main_Item_ChatBot_Pool(pool_size)
    return _main_item_pool
