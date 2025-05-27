import requests
import json
import random
import string


class DifyAgentStreamClient:
    def __init__(self, api_key="app-wmEP04yuHznvhCVASXwacicE", base_url="http://139.210.101.45:12449/v1"):
        """
        初始化 Dify Agent 客户端
        :param api_key: Dify API 密钥
        :param base_url: Dify API 基础地址
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        }

    def chat(self, query, inputs=None, user_id=None, conversation_id=None):
        """
        流式调用 Agent 并处理响应
        :param query: 用户查询内容
        :param inputs: 额外输入参数(可选)
        :param user_id: 用户ID(可选)
        :param conversation_id: 会话ID(可选)
        :return: 返回完整回答和会话ID的字典
        """
        # 构建请求端点
        endpoint = f"{self.base_url}/chat-messages"

        # 准备请求数据
        payload = {
            "inputs": inputs or {},
            "query": query,
            "response_mode": "streaming",
            "user": user_id or f"user_{self._generate_random_id()}",
        }

        if conversation_id:
            payload["conversation_id"] = conversation_id  # 修正拼写错误

        try:
            print(f"\n[Agent] 问题: {query}\n[Agent] 开始响应:",
                  end="\n\n", flush=True)

            # 发送流式请求
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload,
                stream=True,
                timeout=30
            )

            if response.status_code != 200:
                print(f"请求失败: {response.status_code}")
                print(response.text)
                return {"full_answer": None, "conversation_id": None}

            full_answer = ""
            current_conversation_id = None
            answers = []
            for line in response.iter_lines():
                if line.startswith(b'data: '):
                    try:
                        data = json.loads(line[6:])  # 去掉 b'data: ' 前缀

                        # 获取会话ID
                        if 'conversation_id' in data:
                            current_conversation_id = data['conversation_id']

                        if data.get('event') == 'message' and 'answer' in data:
                            answer = data['answer']
                            # full_answer += answer
                            answers.append(answer)
                            # print(answer, end='', flush=True)

                    except json.JSONDecodeError as e:
                        print(f"\nJSON解析错误: {e}")
                        continue

            return {
                "answer": ''.join(answers),
            }

        except requests.exceptions.RequestException as e:
            print(f"\n请求异常: {e}")
            return {"answer": None, "conversation_id": None}

    def _generate_random_id(self):
        """生成随机用户ID"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=8))


# 使用示例
if __name__ == "__main__":
    # 替换为你的实际 API 密钥
    API_KEY = "app-hx7aN6kN684S5XMmjGkyo5Me"
    # API_KEY = "app-4t68JtnHkfdLoOb0tmfmq2Gf"
# app-hx7aN6kN684S5XMmjGkyo5Me
    # 初始化客户端
    client = DifyAgentStreamClient(API_KEY)

    # 示例1: 简单查询
    print("示例1: 简单查询")
    response = client.chat(
        query="联系方式"
    )
    print(f"\n完整回答: {response['full_answer']}")

    # # 示例2: 带上下文的连续对话
    # print("\n\n示例2: 连续对话")

    # # 第一轮对话
    # print("\n第一轮:")
    # response1 = client.stream_agent_response(
    #     query="我想了解新能源汽车行业",
    #     user_id="user_12345",
    # )

    # if response1["conversation_id"]:
    #     # 第二轮对话(使用相同的会话ID)
    #     print("\n第二轮:")
    #     response2 = client.stream_agent_response(
    #         query="请重点分析特斯拉的市场表现",
    #         user_id="user_12345",
    #         conversation_id=response1["conversation_id"]
    #     )
    #     print(f"\n完整回答: {response2['full_answer']}")
