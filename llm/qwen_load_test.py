from locust import HttpUser, task, between, events
import json
import random
from datetime import datetime

# 测试配置
CONCURRENT_USERS = 20  # 并发用户数
ROUNDS = 20           # 每用户请求轮数


class QwenApiUser(HttpUser):
    wait_time = between(1, 3)  # 用户等待时间在1-3秒之间
    host = "http://139.210.101.45:12455"

    # 用户级变量
    request_count = 0

    def on_start(self):
        """用户启动时执行"""
        self.start_time = datetime.now()
        # 使用对象内存地址作为唯一标识
        self.user_id = id(self)
        print(f"用户 {self.user_id} 启动测试")

    def on_stop(self):
        """用户停止时执行"""
        duration = datetime.now() - self.start_time
        print(f"用户 {self.user_id} 完成测试, 共发送 {self.request_count} 请求, 耗时 {duration}")

    @task
    def chat_completion(self):
        """主测试任务"""
        if self.request_count >= ROUNDS:
            self.stop(force=True)  # 完成指定轮数后停止
            return

        headers = {
            "Accept": "application/json",
            "Content-type": "application/json"
        }

        # 参数化请求内容
        questions = [
            "介绍一下你自己",
            "你能做什么?请详细说明",
            "解释一下量子计算的基本原理",
            "写一首关于人工智能的诗",
            "如何学习深度学习?",
            "Python和Java有什么区别?",
            "最新的AI技术有哪些突破?",
            "如何评估一个机器学习模型?",
            "Transformer架构的核心思想是什么?",
            "大语言模型的工作原理是怎样的?"
        ]

        payload = {
            "model": "qwen",
            "messages": [{
                "role": "user",
                "content": random.choice(questions) + " <think>\n"
            }],
            "stream": True,
            "max_token": 1024
        }

        # 发送请求
        with self.client.post(
            "/v1/chat/completions",
            headers=headers,
            data=json.dumps(payload),
            name="Chat Completion",
            catch_response=True
        ) as response:
            self.request_count += 1

            # 验证响应
            if response.status_code != 200:
                response.failure(f"状态码: {response.status_code}")
            else:
                try:
                    data = response.json()
                    if not data.get("choices"):
                        response.failure("响应中缺少choices字段")
                except ValueError:
                    response.failure("无效的JSON响应")

# 测试启动事件


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print(f"\n=== 测试开始 ===\n并发用户: {CONCURRENT_USERS}\n每用户请求轮数: {ROUNDS}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("\n=== 测试结束 ===")


# locust - f llm/qwen_load_test.py - -users 20 \
#  - -spawn-rate 10 --web-host 0.0.0.0