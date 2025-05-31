from locust import HttpUser, task, between, events
import random
import time
import json
import requests
import http.client

# 全局配置
TOTAL_USERS = 20  # 并发用户数
REQUESTS_PER_USER = 20  # 每个用户请求次数
MAX_REQUESTS = TOTAL_USERS * REQUESTS_PER_USER  # 总请求数
TOTAL_REQUESTS = 0  # 当前已完成请求数


class ChatBotUser(HttpUser):
    wait_time = between(1, 3)  # 用户等待时间在1到3秒之间
    host = "http://116.141.0.87:32300"  # 设置基础URL

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request_count = 0
        self.api_key = "d0rabvgvfjfv26hqvk3g"
        self.chat_bot = ChatBot(self.api_key)
        self.questions = [
            "我想办理残疾证业务，咋办啊",
            "我想去哪里可以办呢",
            "需要准备什么材料",
            "办理流程是什么",
            "多久能办好",
            "有什么优惠政策吗",
            "可以网上办理吗",
            "需要本人到场吗",
            "办理费用是多少",
            "残疾证有什么用处"
        ]

    @task
    def chat_test(self):
        """测试聊天接口"""
        global TOTAL_REQUESTS

        if TOTAL_REQUESTS >= MAX_REQUESTS:
            self.environment.runner.stop()
            return

        question = random.choice(self.questions)
        start_time = time.time()
        try:
            # 使用Locust的client记录请求时间
            with self.client.post(
                "/api/proxy/api/v1/chat_query",
                catch_response=True,
                name="chat_query"
            ) as response:
                result = self.chat_bot.chat(question)
                response.success()
                self.request_count += 1
                TOTAL_REQUESTS += 1
                duration = (time.time() - start_time) * 1000  # 转换为毫秒
                print(f"[User-{self.__dict__.get('_id', '?')}] Req-{self.request_count}/{REQUESTS_PER_USER} | "
                      f"Time: {duration:.2f}ms | Total: {TOTAL_REQUESTS}/{MAX_REQUESTS}")
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            print(
                f"[User-{self.__dict__.get('_id', '?')}] Error: {str(e)} | Time: {duration:.2f}ms")
            self.request_count += 1
            TOTAL_REQUESTS += 1
            self.environment.events.request.fire(
                request_type="POST",
                name="chat_query",
                response_time=duration,
                exception=e
            )


class ChatBot:
    def __init__(self, api_key):
        self.user_id = "admin123"
        self.api_key = api_key
        self.host = "116.141.0.87"
        self.port = "32300"
        self.conversation_id = self.create_conversation()

    def create_conversation(self):
        url = f"http://{self.host}:{self.port}/api/proxy/api/v1/create_conversation"
        headers = {"Apikey": self.api_key, "Content-Type": "application/json"}
        data = {"Inputs": {"user_id": self.user_id}, "UserID": self.user_id}
        try:
            response = requests.post(
                url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            return response.json()['Conversation']['AppConversationID']
        except Exception as e:
            raise Exception(f"创建会话失败: {str(e)}")

    def chat(self, query):
        result = ""
        headers = {
            'Apikey': self.api_key,
            'Accept': 'text/event-stream',
            'Content-Type': 'application/json'
        }
        data = {
            'Query': query,
            'AppConversationID': self.conversation_id,
            'ResponseMode': 'streaming',
            'UserID': self.user_id,
        }

        try:
            connection = http.client.HTTPConnection(
                self.host, self.port, timeout=10)
            connection.request('POST', '/api/proxy/api/v1/chat_query',
                               body=json.dumps(data), headers=headers)
            response = connection.getresponse()

            if response.status == 200:
                for line in response:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data:data:'):
                        try:
                            json_data = json.loads(line[10:])
                            if json_data['event'] == "message":
                                result += json_data['answer']
                        except json.JSONDecodeError:
                            continue
            else:
                raise Exception(f"HTTP {response.status}: {response.reason}")

        except Exception as e:
            raise Exception(f"聊天请求失败: {str(e)}")
        finally:
            connection.close()

        return {"answer": result}

# 事件监听器


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("\n" + "="*50)
    print(
        f"测试启动 | 目标: {TOTAL_USERS}并发 × {REQUESTS_PER_USER}轮 = {MAX_REQUESTS}请求")
    print("="*50)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("\n" + "="*50)
    print(f"测试完成 | 总请求: {TOTAL_REQUESTS}/{MAX_REQUESTS}")
    if hasattr(environment, 'runner') and hasattr(environment.runner, 'stats'):
        stats = environment.runner.stats
        if stats.total.num_requests > 0:
            print(f"平均响应时间: {stats.total.avg_response_time:.2f}ms")
            print(f"最大响应时间: {stats.total.max_response_time:.2f}ms")
            print(f"最小响应时间: {stats.total.min_response_time or 0:.2f}ms")
            print(f"请求成功率: {(1-stats.total.fail_ratio)*100:.2f}%")
    print("="*50)
