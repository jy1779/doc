# 部署master组件

下载二进制文件

https://github.com/kubernetes/kubernetes/blob/master/CHANGELOG-1.10.md#v1108

https://dl.k8s.io/v1.10.8/kubernetes-server-linux-amd64.tar.gz

### 部署api-server

移动组件到 /opt/kubernetes/bin/

```shell
mv kube-controller-manager kube-apiserver kube-scheduler /opt/kubernetes/bin/
chmod +x /opt/kubernetes/bin/*
cp token.csv /opt/kubernetes/cfg/
cp ssl/ca-key.pem /opt/kubernetes/ssl/

#apiserver 生成启动参数文件及创建启动文件
root@k8s-master:~# cat apiserver.sh 
#!/bin/bash

MASTER_ADDRESS=${1:-"192.168.1.195"}
ETCD_SERVERS=${2:-"http://127.0.0.1:2379"}

cat <<EOF >/opt/kubernetes/cfg/kube-apiserver

KUBE_APISERVER_OPTS="--logtostderr=true \\
--v=4 \\
--etcd-servers=${ETCD_SERVERS} \\
--insecure-bind-address=127.0.0.1 \\
--bind-address=${MASTER_ADDRESS} \\
--insecure-port=8080 \\
--secure-port=6443 \\
--advertise-address=${MASTER_ADDRESS} \\
--allow-privileged=true \\
--service-cluster-ip-range=10.10.10.0/24 \\
--admission-control=NamespaceLifecycle,LimitRanger,SecurityContextDeny,ServiceAccount,ResourceQuota,NodeRestriction \
--authorization-mode=RBAC,Node \\
--kubelet-https=true \\
--enable-bootstrap-token-auth \\
--token-auth-file=/opt/kubernetes/cfg/token.csv \\
--service-node-port-range=80-50000 \\
--tls-cert-file=/opt/kubernetes/ssl/server.pem  \\
--tls-private-key-file=/opt/kubernetes/ssl/server-key.pem \\
--client-ca-file=/opt/kubernetes/ssl/ca.pem \\
--service-account-key-file=/opt/kubernetes/ssl/ca-key.pem \\
--etcd-cafile=/opt/kubernetes/ssl/ca.pem \\
--etcd-certfile=/opt/kubernetes/ssl/server.pem \\
--etcd-keyfile=/opt/kubernetes/ssl/server-key.pem"

EOF

cat <<EOF >/lib/systemd/system/kube-apiserver.service
[Unit]
Description=Kubernetes API Server
Documentation=https://github.com/kubernetes/kubernetes

[Service]
EnvironmentFile=-/opt/kubernetes/cfg/kube-apiserver
ExecStart=/opt/kubernetes/bin/kube-apiserver \$KUBE_APISERVER_OPTS
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

systemctl enable kube-apiserver
systemctl start kube-apiserver

#执行脚本
./apiserver.sh 192.168.1.67 https://192.168.1.67:2379,https://192.168.1.69:2379
#生成启动参数文件
root@k8s-master:~# cat /opt/kubernetes/cfg/kube-apiserver

KUBE_APISERVER_OPTS="--logtostderr=true \
--v=4 \
--etcd-servers=https://192.168.1.67:2379,https://192.168.1.69:2379 \
--insecure-bind-address=127.0.0.1 \
--bind-address=192.168.1.67 \
--insecure-port=8080 \
--secure-port=6443 \
--advertise-address=192.168.1.67 \
--allow-privileged=true \
--service-cluster-ip-range=10.10.10.0/24 \
--admission-control=NamespaceLifecycle,LimitRanger,SecurityContextDeny,ServiceAccount,ResourceQuota,NodeRestriction --authorization-mode=RBAC,Node \
--kubelet-https=true \
--enable-bootstrap-token-auth \
--token-auth-file=/opt/kubernetes/cfg/token.csv \
--service-node-port-range=80-50000 \
--tls-cert-file=/opt/kubernetes/ssl/server.pem  \
--tls-private-key-file=/opt/kubernetes/ssl/server-key.pem \
--client-ca-file=/opt/kubernetes/ssl/ca.pem \
--service-account-key-file=/opt/kubernetes/ssl/ca-key.pem \
--etcd-cafile=/opt/kubernetes/ssl/ca.pem \
--etcd-certfile=/opt/kubernetes/ssl/server.pem \
--etcd-keyfile=/opt/kubernetes/ssl/server-key.pem"
#生成启动apiserver文件
root@k8s-master:~# cat /lib/systemd/system/kube-apiserver.service 
[Unit]
Description=Kubernetes API Server
Documentation=https://github.com/kubernetes/kubernetes

[Service]
EnvironmentFile=-/opt/kubernetes/cfg/kube-apiserver
ExecStart=/opt/kubernetes/bin/kube-apiserver $KUBE_APISERVER_OPTS
Restart=on-failure

[Install]
WantedBy=multi-user.target

```

启动参数说明

```shell
KUBE_APISERVER_OPTS="--logtostderr=true \ #启动错误日志
--v=4 \ #日志级别
--etcd-servers=https://192.168.1.67:2379,https://192.168.1.69:2379 \ #etcd的service地址 
--insecure-bind-address=127.0.0.1 \ #非安全端口
--bind-address=192.168.1.67 \ #绑定安全端口
--insecure-port=8080 \ #非安全端口
--secure-port=6443 \   #绑定安全端口
--advertise-address=192.168.1.67 \ #k8s集群通信地址
--allow-privileged=true \ #允许授权,允许容器创建时启用该授权
--service-cluster-ip-range=10.10.10.0/24 \  #k8s集群的vip地址范围
--admission-control=NamespaceLifecycle,LimitRanger,SecurityContextDeny,ServiceAccount,ResourceQuota,NodeRestriction --authorization-mode=RBAC,Node \  #授权策略
--kubelet-https=true \ #kubelet启用https访问
--enable-bootstrap-token-auth \ #启用token认证
--token-auth-file=/opt/kubernetes/cfg/token.csv \ #token文件
--service-node-port-range=80-50000 \ #k8s集群端口范围
###以下是集群需要使用的证书
--tls-cert-file=/opt/kubernetes/ssl/server.pem  \
--tls-private-key-file=/opt/kubernetes/ssl/server-key.pem \
--client-ca-file=/opt/kubernetes/ssl/ca.pem \
--service-account-key-file=/opt/kubernetes/ssl/ca-key.pem \
###以下是etcd的证书，api-server访问etcd需要使用的
--etcd-cafile=/opt/kubernetes/ssl/ca.pem \
--etcd-certfile=/opt/kubernetes/ssl/server.pem \
--etcd-keyfile=/opt/kubernetes/ssl/server-key.pem"
```



### 部署controller-manager

```shell
root@k8s-master:~# cat controller-manager.sh 
#!/bin/bash

MASTER_ADDRESS=${1:-"127.0.0.1"}

cat <<EOF >/opt/kubernetes/cfg/kube-controller-manager


KUBE_CONTROLLER_MANAGER_OPTS="--logtostderr=true \\
--v=4 \\
--master=${MASTER_ADDRESS}:8080 \\
--leader-elect=true \\
--address=127.0.0.1 \\
--service-cluster-ip-range=10.10.10.0/24 \\
--cluster-name=kubernetes \\
--cluster-signing-cert-file=/opt/kubernetes/ssl/ca.pem \\
--cluster-signing-key-file=/opt/kubernetes/ssl/ca-key.pem  \\
--service-account-private-key-file=/opt/kubernetes/ssl/ca-key.pem \\
--root-ca-file=/opt/kubernetes/ssl/ca.pem"

EOF

cat <<EOF >/lib/systemd/system/kube-controller-manager.service
[Unit]
Description=Kubernetes Controller Manager
Documentation=https://github.com/kubernetes/kubernetes

[Service]
EnvironmentFile=-/opt/kubernetes/cfg/kube-controller-manager
ExecStart=/opt/kubernetes/bin/kube-controller-manager \$KUBE_CONTROLLER_MANAGER_OPTS
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

systemctl enable kube-controller-manager
systemctl start kube-controller-manager

#执行脚本
root@k8s-master:~# ./controller-manager.sh 127.0.0.1
#启动参数文件
root@k8s-master:~# cat /opt/kubernetes/cfg/kube-controller-manager 


KUBE_CONTROLLER_MANAGER_OPTS="--logtostderr=true \
--v=4 \
--master=127.0.0.1:8080 \
--leader-elect=true \
--address=127.0.0.1 \
--service-cluster-ip-range=10.10.10.0/24 \
--cluster-name=kubernetes \
--cluster-signing-cert-file=/opt/kubernetes/ssl/ca.pem \
--cluster-signing-key-file=/opt/kubernetes/ssl/ca-key.pem  \
--service-account-private-key-file=/opt/kubernetes/ssl/ca-key.pem \
--root-ca-file=/opt/kubernetes/ssl/ca.pem"
#启动文件
root@k8s-master:~# cat /lib/systemd/system/kube-controller-manager.service 
[Unit]
Description=Kubernetes Controller Manager
Documentation=https://github.com/kubernetes/kubernetes

[Service]
EnvironmentFile=-/opt/kubernetes/cfg/kube-controller-manager
ExecStart=/opt/kubernetes/bin/kube-controller-manager $KUBE_CONTROLLER_MANAGER_OPTS
Restart=on-failure

[Install]
WantedBy=multi-user.target

```

### 部署scheduler

```shell
root@k8s-master:~# cat scheduler.sh 
#!/bin/bash

MASTER_ADDRESS=${1:-"127.0.0.1"}

cat <<EOF >/opt/kubernetes/cfg/kube-scheduler

KUBE_SCHEDULER_OPTS="--logtostderr=true \\
--v=4 \\
--master=${MASTER_ADDRESS}:8080 \\
--leader-elect"

EOF

cat <<EOF >/lib/systemd/system/kube-scheduler.service
[Unit]
Description=Kubernetes Scheduler
Documentation=https://github.com/kubernetes/kubernetes

[Service]
EnvironmentFile=-/opt/kubernetes/cfg/kube-scheduler
ExecStart=/opt/kubernetes/bin/kube-scheduler \$KUBE_SCHEDULER_OPTS
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

systemctl enable kube-scheduler
systemctl start kube-scheduler
#执行脚本
root@k8s-master:~# ./scheduler.sh 127.0.0.1
#启动参数文件
root@k8s-master:~# cat /opt/kubernetes/cfg/kube-scheduler 

KUBE_SCHEDULER_OPTS="--logtostderr=true \
--v=4 \
--master=127.0.0.1:8080 \
--leader-elect"
#启动文件
root@k8s-master:~# cat /lib/systemd/system/kube-scheduler.service 
[Unit]
Description=Kubernetes Scheduler
Documentation=https://github.com/kubernetes/kubernetes

[Service]
EnvironmentFile=-/opt/kubernetes/cfg/kube-scheduler
ExecStart=/opt/kubernetes/bin/kube-scheduler $KUBE_SCHEDULER_OPTS
Restart=on-failure

[Install]
WantedBy=multi-user.target

```

### 检测集群情况

```shell
root@k8s-master:~# kubectl get cs
NAME                 STATUS    MESSAGE              ERROR
scheduler            Healthy   ok                   
controller-manager   Healthy   ok                   
etcd-1               Healthy   {"health": "true"}   
etcd-0               Healthy   {"health": "true"}  
```

