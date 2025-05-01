import requests
import http.client
import json
import time


class ChatBot:
    def __init__(self, api_key):
        '''
        初始化 ChatBot 类的实例。
        参数：
        - user_id (str): 用户 ID。
        - api_key (str): API 密钥。
        - host (str): 主机地址。
        - port (str): 端口号。
        返回：

        '''
        self.user_id = "admin123"
        self.api_key = api_key
        self.host = "115.190.98.254"
        self.port = "80"
        # 在初始化时创建一个新的对话
        self.conversation_id = self.create_conversation()

    def create_conversation(self):
        '''
        创建一个新的对话。
        参数：
        无
        返回：
        str: 新创建的对话的 ID。
        '''
        url = f"http://{self.host}:{self.port}/api/proxy/api/v1/create_conversation"
        headers = {"Apikey": self.api_key, "Content-Type": "application/json"}
        data = {"Inputs": {"user_id": self.user_id}, "UserID": self.user_id}
        response = requests.post(url, headers=headers, json=data)
        # print(response.text)
        conversation = json.loads(response.text)
        return conversation['Conversation']['AppConversationID']

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
        # print(data)
        start_time = time.time()
        connection = http.client.HTTPConnection(
            host=self.host, port=self.port)
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
                    except Exception as e:
                        print(str(e))
                        continue
        else:
            print(f"Failed to connect: {response.status}, {response.reason}")
        connection.close()
        end_time = time.time()
        all_duration = end_time - start_time
        formatted_result = "{:.2f}".format(all_duration)
        result_obj = {"answer": result, "duration": formatted_result}
        # print(result_obj)
        return result_obj


if __name__ == "__main__":
    # user_id = "zcssjcyfzyxgs_2992"
    # api_key = "cv0hrrkfl93b530prue0"
    # host = "hiagent.volcenginepaas.com"

    user_id = "admin123"
    api_key = "d091308a8cgtr0h4npng"
    # api_key = "d090t37292p9imkl63j0"
    host = "115.190.98.254"
    port = "80"
    chat_bot = ChatBot(user_id, api_key, host, port)    
    # result = chat_bot.chat("我想办理残疾证业务，咋办啊")
    # result = chat_bot.chat("我想办理残疾证业务，咋办啊")
    result = chat_bot.chat("我想去哪里可以办呢")
    print(result)
