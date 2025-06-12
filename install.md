### install docker

sudo apt install docker.io -y


### install python


### config source
```
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json <<-'EOF'
{
  "registry-mirrors": ["https://niyfvllo.mirror.aliyuncs.com"]
}
EOF

sudo systemctl daemon-reload
sudo systemctl restart docker
```



docker run -itd --privileged \
--name mindie \
--ipc=host \
--network=host \
--device=/dev/davinci0 \
--device=/dev/davinci1 \
--device=/dev/davinci2 \
--device=/dev/davinci3 \
--device=/dev/davinci4 \
--device=/dev/davinci5 \
--device=/dev/davinci6 \
--device=/dev/davinci7 \
--device=/dev/davinci_manager \
--device=/dev/devmm_svm \
--device=/dev/hisi_hdc \
-v /usr/local/dcmi:/usr/local/dcmi \
-v /usr/local/bin/npu-smi:/usr/local/bin/npu-smi \
-v /usr/local/Ascend/driver/lib64/common:/usr/local/Ascend/driver/lib64/common \
-v /usr/local/Ascend/driver/lib64/driver:/usr/local/Ascend/driver/lib64/driver \
-v /etc/ascend_install.info:/etc/ascend_install.info \
-v /etc/localtime:/etc/localtime \
-v /etc/vnpu.cfg:/etc/vnpu.cfg \
-v /usr/local/Ascend/driver/version.info:/usr/local/Ascend/driver/version.info \
swr.cn-northeast-228.ccaicc.com/ccaicc-bms-910b/mindie:1.0 /bin/bash


### 56 rasa后端：

```
(rasa) root@ubuntu56:~# tmux ls
n8n: 1 windows (created Sun Jun  8 06:57:39 2025)
rasa-action: 1 windows (created Sun Apr 20 21:48:04 2025)
rasa-core1: 1 windows (created Sat May 24 07:00:40 2025)
rasa-core2: 1 windows (created Sat May 24 07:02:47 2025)
rasa-core3: 1 windows (created Sat May 24 07:03:49 2025)
```

```
(rasa) root@ubuntu56:~# docker ps -a 
CONTAINER ID   IMAGE                COMMAND                  CREATED       STATUS                   PORTS                                                                                            NAMES
ecdffea45b15   neo4j:latest         "tini -g -- /startup…"   2 weeks ago   Up 4 days                0.0.0.0:7474->7474/tcp, :::7474->7474/tcp, 7473/tcp, 0.0.0.0:7687->7687/tcp, :::7687->7687/tcp   neo4j
```

#### rasa集群

```
SANIC_WORKERS=8 SANIC_ACCESS_LOG=false SANIC_REQUEST_MAX_SIZE=100000000 SANIC_REQUEST_TIMEOUT=120 rasa run   --enable-api   --cors "*"   --model models/latest.tar.gz   --endpoints endpoints.yml   --credentials credentials.yml   --log-file rasa.log   --port 5006 --debug
```

### rasa 前端

```
(rasa) root@ubuntu12:~# tmux ls
proxy: 1 windows (created Fri May 16 13:57:24 2025)
rasa-action: 1 windows (created Wed May 14 21:43:39 2025)
rasa-api: 1 windows (created Fri May 23 12:08:39 2025)
streamlit: 1 windows (created Mon May 19 10:03:15 2025)
web: 1 windows (created Thu May 15 13:27:08 2025)
```
```
uvicorn app:app --workers 12 --host 0.0.0.0 --port 5678 --limit-concurrency 1000 --timeout-keep-alive 30
```
