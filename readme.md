 
    - 二道区
    - 双阳区
    - 九台区
    - 榆树市
    - 德惠市
    - 净月

    这些数据需要缩写的语音输入

目前存在的问题：

1. 用户不清楚机器人可以提供哪些服务，不知道机器人服务的边界。（llm识别）
2. 缺少帮助，用户不知道该如何使用系统
3. 大部分的都是问服务中心的电话、地址、上班时间的
4. 通过中继号判断用户的区域
5. 缺少语音上的矫正 （llm）
6. 通话记录的存储是否要我们独自保存（私有化联通）

业务上的问题：
1. 新区的数据是独立，现在的知识库没有新区数据（是否可以合并）
2. 十多个办理项和情形是重复的
3. 办理地址夸区域的， 中韩是宽城的，汽开区是绿园的（无）
4. 儿童办理护照（16岁以下）  （后）

解决办法：
1. 增加对服务中心基本信息的查询功能（higent agent）
2. 考虑进行电话回访（是否自动语音）（后）
3. 增加帮助的语音服务（不做）
4. 通话记录的llm分析，形成report（或者elk分析，chatBI）
5. 增加一个新的智能体，用于对用户输入语句的矫正（增加了延迟时间）

后续技术方向：

1. rasa pro
2. mcp的技术支持
3. dify ,n8n ,ragflow 
4. suld 910b embeding, rerank, deepseek. 

和呼入电话相关区域相关:


1. 开发智能体，解决用户查询电话，上班时间，办理地点的基础信息
2. 增加智能体，统一放在rasa前端之前，对用户的意图进行识别。（流程需要讨论）
3. 增加对网点号码的识别，直接认为用户的区域就是网点号码的区域
4. 增加10个业务主项识别的智能体，测试智能体的并发量

"neo4j-aura": {
      "timeout": 60,
      "type": "stdio",
      "command": "uvx",
      "args": [
        "mcp-neo4j-cypher@0.2.1"
      ],
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "password",
        "NEO4J_DATABASE": "neo4j"
      }
    }
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USERNAME="neo4j"
export NEO4J_PASSWORD="password"
export NEO4J_DATABASE="neo4j"
export UV_INDEX="https://pypi.tuna.tsinghua.edu.cn/simple"
uvx "mcp-neo4j-cypher@0.2.1"
