# 部署etcd集群

### k8s-master部署etcd

```shell
root@k8s-master:~# ls
etcd.sh  etcd-v3.2.12-linux-amd64.tar.gz  ssl
root@k8s-master:~# tar xf etcd-v3.2.12-linux-amd64.tar.gz 
root@k8s-master:~# ls
etcd.sh  etcd-v3.2.12-linux-amd64  etcd-v3.2.12-linux-amd64.tar.gz  ssl
root@k8s-master:~# ls etcd-v3.2.12-linux-amd64
Documentation  etcd  etcdctl  README-etcdctl.md  README.md  READMEv2-etcdctl.md
root@k8s-master:~# cp -a  etcd-v3.2.12-linux-amd64/etcd /opt/kubernetes/bin/
root@k8s-master:~# cp -a  etcd-v3.2.12-linux-amd64/etcdctl /opt/kubernetes/bin/
# 创建启动etcd配置文件
root@k8s-master:~# cat /opt/kubernetes/cfg/etcd
#[Member]
ETCD_NAME="etcd01"  #指定etcd名称
ETCD_DATA_DIR="/var/lib/etcd/default.etcd"  #数据目录，存储etcd数据
ETCD_LISTEN_PEER_URLS="https://192.168.1.67:2380"  #集群通信端口，监听客户端地址。
ETCD_LISTEN_CLIENT_URLS="https://192.168.1.67:2379" #数据端口，请求该接口返回数据

#[Clustering]
ETCD_INITIAL_ADVERTISE_PEER_URLS="https://192.168.1.67:2380" #集群监听该接口
ETCD_ADVERTISE_CLIENT_URLS="https://192.168.1.67:2379" #数据端口
ETCD_INITIAL_CLUSTER="etcd01=https://192.168.1.67:2380,etcd02=https://192.168.1.69:2380" #集群节点
ETCD_INITIAL_CLUSTER_TOKEN="etcd-cluster"  #集群的token，自定义
ETCD_INITIAL_CLUSTER_STATE="new"  #状态，第一次建立可以写new
#创建etcd服务
root@k8s-master:~# cat  /lib/systemd/system/etcd.service
[Unit]
Description=Etcd Server
After=network.target
After=network-online.target
Wants=network-online.target

[Service]
Type=notify
EnvironmentFile=-/opt/kubernetes/cfg/etcd
ExecStart=/opt/kubernetes/bin/etcd \
--name=${ETCD_NAME} \
--data-dir=${ETCD_DATA_DIR} \
--listen-peer-urls=${ETCD_LISTEN_PEER_URLS} \
--listen-client-urls=${ETCD_LISTEN_CLIENT_URLS},http://127.0.0.1:2379 \
--advertise-client-urls=${ETCD_ADVERTISE_CLIENT_URLS} \
--initial-advertise-peer-urls=${ETCD_INITIAL_ADVERTISE_PEER_URLS} \
--initial-cluster=${ETCD_INITIAL_CLUSTER} \
--initial-cluster-token=${ETCD_INITIAL_CLUSTER_TOKEN} \
--initial-cluster-state=new \
--cert-file=/opt/kubernetes/ssl/server.pem \
--key-file=/opt/kubernetes/ssl/server-key.pem \
--peer-cert-file=/opt/kubernetes/ssl/server.pem \
--peer-key-file=/opt/kubernetes/ssl/server-key.pem \
--trusted-ca-file=/opt/kubernetes/ssl/ca.pem \
--peer-trusted-ca-file=/opt/kubernetes/ssl/ca.pem
Restart=on-failure
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target

#拷贝证书文件
root@k8s-master:~# cp ssl/ca.pem /opt/kubernetes/ssl/
root@k8s-master:~# cp ssl/server* /opt/kubernetes/ssl/
root@k8s-master:~# ls /opt/kubernetes/ssl/
ca.pem  server-key.pem  server.pem

#启动etcd服务
systemctl enable etcd.service
service etcd start #启动会卡住后期解决

```

### k8s-node1部署etcd

```shell
#将master的etcd需要用到的文件拷贝到node
root@k8s-master:~# scp /opt/kubernetes/bin/etcd* 192.168.1.69:/opt/kubernetes/bin/
etcd                                                                                                                                                       100%   17MB  17.0MB/s   00:00    
etcdctl                                                                                                                                                    100%   15MB  14.5MB/s   00:00    

root@k8s-master:~# scp /opt/kubernetes/cfg/etcd  192.168.1.69:/opt/kubernetes/cfg/
etcd                                                                                                                                                       100%  470     0.5KB/s   00:00    
root@k8s-master:~# scp /opt/kubernetes/ssl/*  192.168.1.69:/opt/kubernetes/ssl/
ca.pem                                                                                                                                                     100% 1363     1.3KB/s   00:00    
server-key.pem                                                                                                                                             100% 1679     1.6KB/s   00:00    
server.pem                                                                                                                                                 100% 1619     1.6KB/s   00:00 
root@k8s-master:~# scp /lib/systemd/system/etcd.service   192.168.1.69:/lib/systemd/system/
etcd.service                                                                                                                                               100% 1022     1.0KB/s   00:00    

#修改etc启动配置文件
root@k8s-node1:~# cat /opt/kubernetes/cfg/etcd 
#[Member]
ETCD_NAME="etcd02"
ETCD_DATA_DIR="/var/lib/etcd/default.etcd"
ETCD_LISTEN_PEER_URLS="https://192.168.1.69:2380"
ETCD_LISTEN_CLIENT_URLS="https://192.168.1.69:2379"

#[Clustering]
ETCD_INITIAL_ADVERTISE_PEER_URLS="https://192.168.1.69:2380"
ETCD_ADVERTISE_CLIENT_URLS="https://192.168.1.69:2379"
ETCD_INITIAL_CLUSTER="etcd01=https://192.168.1.67:2380,etcd02=https://192.168.1.69:2380"
ETCD_INITIAL_CLUSTER_TOKEN="etcd-cluster"
ETCD_INITIAL_CLUSTER_STATE="new"
#启动etcd
root@k8s-node1:~# systemctl enable etcd.service
Created symlink from /etc/systemd/system/multi-user.target.wants/etcd.service to /lib/systemd/system/etcd.service.
root@k8s-node1:~# service etcd start
root@k8s-node1:~# ps -ef |grep etcd
root      20919      1  6 15:33 ?        00:00:00 /opt/kubernetes/bin/etcd --name=etcd02 --data-dir=/var/lib/etcd/default.etcd --listen-peer-urls=https://192.168.1.69:2380 --listen-client-urls=https://192.168.1.69:2379,http://127.0.0.1:2379 --advertise-client-urls=https://192.168.1.69:2379 --initial-advertise-peer-urls=https://192.168.1.69:2380 --initial-cluster=etcd01=https://192.168.1.67:2380,etcd02=https://192.168.1.69:2380 --initial-cluster-token=etcd01=https://192.168.1.67:2380,etcd02=https://192.168.1.69:2380 --initial-cluster-state=new --cert-file=/opt/kubernetes/ssl/server.pem --key-file=/opt/kubernetes/ssl/server-key.pem --peer-cert-file=/opt/kubernetes/ssl/server.pem --peer-key-file=/opt/kubernetes/ssl/server-key.pem --trusted-ca-file=/opt/kubernetes/ssl/ca.pem --peer-trusted-ca-file=/opt/kubernetes/ssl/ca.pem
root      20930   1301  0 15:33 pts/0    00:00:00 grep --color=auto etcd

```

### 测试etcd集群

```shell
root@k8s-master:~/ssl# /opt/kubernetes/bin/etcdctl --ca-file=ca.pem --cert-file=server.pem --key-file=server-key.pem --endpoints="https://192.168.1.67:2379,https://192.168.1.69:2379" cluster-health
member b7ef410b167a4462 is healthy: got healthy result from https://192.168.1.69:2379
member d8916b657c5dc08f is healthy: got healthy result from https://192.168.1.67:2379
cluster is healthy
```

