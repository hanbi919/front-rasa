### agent type
<!-- 事项匹配机器人 -->
APPKEY：d090ot7292p9imkl634g
APIKEY：d090t37292p9imkl63j0

<!-- 意图匹配机器人 -->
APPKEY：d090vj8a8cgtr0h4npjg
APIKEY：d091308a8cgtr0h4npng


### reask

追问问题:
请问您是要了解哪一项办理主项内容呢?1:住房公积金汇缴 2:租赁自住住房提取住房公积金 3:离休、退休提取住房公积金 4:住房公积金单位缴存登记
追问回复:
单位缴存


请问您是要了解哪一项办理主项内容呢？1：排污许可核发 2：排污许可变更 3：排污许可注销


### 运行main.py

uvicorn main:app --workers 4 --host 0.0.0.0 --port 5678

### 工具列表

1. tools/check.py 用于利用智能体对泛化的内容进行检查

http://115.190.98.254/product/llm/chat/d0fn42n292p9imkl908g

### change chat
 packages/ui/src/index.html 
 server-url ="http://116.141.0.116:5005

 git diff examples/react/src/App.tsx
 serverUrl="https://localhost:5005/webhooks/rest/webhook

 examples/html/index.html


 #### proxy

 uvicorn app:app --workers 12 --host 0.0.0.0 --port 5678

#### rasa-api
 SANIC_WORKERS=8 rasa run --enable-api --cors "*" --debug

#### rasa-action
export ACTION_SERVER_SANIC_WORKERS=8
rasa run actions 

#### neo4j

docker run --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -v neo4j_data:/data \
  -v neo4j_logs:/logs \
  -v neo4j_import:/var/lib/neo4j/import \
  --env NEO4J_AUTH=neo4j/password \
  --env NEO4J_dbms_connector_bolt_thread__pool__min__size=20 \
  --env NEO4J_dbms_connector_bolt_thread__pool__max__size=50 \
  --env NEO4J_dbms_memory_heap_initial__size=4G \
  --env NEO4J_dbms_memory_heap_max__size=8G \
  --env NEO4J_dbms_memory_pagecache_size=8G \
  --restart unless-stopped \
  --memory 16g \
  --cpus 8 \
  -d neo4j:latest



  uvicorn app:app --workers 12 --host 0.0.0.0 --port 5678 --limit-concurrency 1000 --timeout-keep-alive 30



  pattern = r'用户问题："(.+?)"，用户标识："(.+?)"'


  gunicorn -k uvicorn.workers.UvicornWorker \
  -w 4 \
  -b :5005 \
  --timeout 120 \
  rasa.__main__:app
    