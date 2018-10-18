# 二进制文件部署kubernetes集群

## 1.1 部署Kubernetes集群Master

> 服务器资源配置，仅仅适合测试部署使用

| 服务器 | IP           | 配置                               | 备注                  |
| ------ | ------------ | ---------------------------------- | --------------------- |
| master | 192.168.1.72 | 系统：ubuntu 16.04 CPU：1 内存：1G | k8s集群master、etcd-0 |
| node01 | 192.168.1.73 | 系统：ubuntu 16.04 CPU：1 内存：1G | k8s集群node01、etcd-1 |
| node02 | 192.168.1.74 | 系统：ubuntu 16.04 CPU：1 内存：1G | k8s集群node02、etcd-2 |

### 1.1.1 安装Docker

```shell
# 关闭防火墙
ufw disable && ufw status
# 执行脚本安装docker
curl -s  https://raw.githubusercontent.com/jy1779/docker/master/install/aliyun_docker_install.sh | bash
# 修改docker.server参数
LINE=$(grep -n ExecStart /lib/systemd/system/docker.service|awk -F : '{print $1}')
EXECSTARTPOST='ExecStartPost=/sbin/iptables -I FORWARD -s 0.0.0.0/0 -j ACCEPT'
sed "$LINE a$EXECSTARTPOST" -i /lib/systemd/system/docker.service
# 重新加载docker.server及重启docker服务
systemctl daemon-reload && service docker restart
```

### 1.1.2 生成配置文件及根证书

```shell
# 添加内核参数
# 参数说明：
# Controls IP packet forwarding
net.ipv4.ip_forward = 1
# Enable netfilter on bridges.
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1

# 执行命令，添加内核参数
cat <<EOF > /etc/sysctl.d/k8s.conf
net.ipv4.ip_forward = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
EOF

# 使内核参数生效
sysctl -p /etc/sysctl.d/k8s.conf
# 如提示以下报错，则执行：modprobe br_netfilter
sysctl: cannot stat /proc/sys/net/bridge/bridge-nf-call-ip6tables: No such file or directory
sysctl: cannot stat /proc/sys/net/bridge/bridge-nf-call-iptables: No such file or directory

# 添加hosts文件
echo -e "192.168.1.72 master\n192.168.1.73 node01\n192.168.1.74 node02" >> /etc/hosts

# 获取k8s二进制文件及配置文件
# kubernetes.git 并非官网的文件，是自定义安装k8s集群所需的文件
root@master:~# git clone https://code.aliyun.com/jy1779/kubernetes.git

# 解压k8s二进制文件，并添加到系统环境变量
root@master:~# tar xf ./kubernetes/kubernetes-bins.tar.gz -C /usr/local/sbin/ && rm -f ./kubernetes/kubernetes-bins.tar.gz
root@master:~# echo 'export PATH=$PATH:/usr/local/sbin/kubernetes-bins' >> /etc/profile && source /etc/profile

# 检测环境变量
root@master:~# which kubectl 
/usr/local/sbin/kubernetes-bins/kubectl

# 生成配置文件
cd /root/kubernetes/kubernetes-starter/
# 修改配置文件
vim config.properties

#kubernetes二进制文件目录,eg: /home/michael/bin
BIN_PATH=/usr/local/sbin/kubernetes-bins

#当前节点ip, eg: 192.168.1.102
NODE_IP=192.168.1.72

#etcd服务集群列表, eg: http://192.168.1.102:2379
#如果已有etcd集群可以填写现有的。没有的话填写：http://${MASTER_IP}:2379 （MASTER_IP自行替换成自己的主节点ip）
ETCD_ENDPOINTS=https://192.168.1.72:2379,https://192.168.1.73:2379,https://192.168.1.74:2379

#kubernetes主节点ip地址, eg: 192.168.1.102
MASTER_IP=192.168.1.72
root@master:~/kubernetes/kubernetes-starter# ./gen-config.sh with-ca
====替换变量列表====
BIN_PATH=/usr/local/sbin/kubernetes-bins
NODE_IP=192.168.1.72
ETCD_ENDPOINTS=https://192.168.1.72:2379,https://192.168.1.73:2379,https://192.168.1.74:2379
MASTER_IP=192.168.1.72
====================
====替换配置文件====
all-node/kube-calico.service
ca/admin/admin-csr.json
ca/ca-config.json
ca/ca-csr.json
ca/calico/calico-csr.json
ca/etcd/etcd-csr.json
ca/kube-proxy/kube-proxy-csr.json
ca/kubernetes/kubernetes-csr.json
master-node/etcd.service
master-node/kube-apiserver.service
master-node/kube-controller-manager.service
master-node/kube-scheduler.service
services/kube-dashboard.yaml
services/kube-dns.yaml
worker-node/10-calico.conf
worker-node/kubelet.service
worker-node/kube-proxy.service
=================
配置生成成功，位置: /root/kubernetes/kubernetes-starter/target

# 安装cfssl
wget -q --show-progress --https-only --timestamping \
  https://pkg.cfssl.org/R1.2/cfssl_linux-amd64 \
  https://pkg.cfssl.org/R1.2/cfssljson_linux-amd64
# 修改为可执行权限
chmod +x cfssl_linux-amd64 cfssljson_linux-amd64
# 移动到bin目录
mv cfssl_linux-amd64 /usr/local/bin/cfssl
mv cfssljson_linux-amd64 /usr/local/bin/cfssljson
# 验证
cfssl version

# 生成根证书
# 创建目录存放ca证书
mkdir -p /etc/kubernetes/ca
# 提示：ca-config.json、ca-csr.json事先已经准备好，可修改，也可以自己生成
# 复制ca文件
cp ~/kubernetes/kubernetes-starter/target/ca/ca-config.json /etc/kubernetes/ca
cp ~/kubernetes/kubernetes-starter/target/ca/ca-csr.json /etc/kubernetes/ca
# 生成证书和密钥
cd /etc/kubernetes/ca
cfssl gencert -initca ca-csr.json | cfssljson -bare ca
# 查看证书和密钥
root@master:/etc/kubernetes/ca# ls
ca-config.json  ca.csr  ca-csr.json  ca-key.pem  ca.pem
```

### 1.1.3 部署Etcd

> etcd节点需要提供给其他服务访问，就要验证其他服务的身份，所以需要一个标识自己监听服务的server证书，当有多个etcd节点的时候也需要client证书与etcd集群其他节点交互，当然也可以client和server使用同一个证书因为它们本质上没有区别。

```shell
# 创建存放etcd证书的目录
mkdir -p /etc/kubernetes/ca/etcd
# 复制etcd证书配置
cp ~/kubernetes/kubernetes-starter/target/ca/etcd/etcd-csr.json /etc/kubernetes/ca/etcd/
cd /etc/kubernetes/ca/etcd/
# 使用根证书(ca.pem)签发etcd证书
cfssl gencert \
        -ca=/etc/kubernetes/ca/ca.pem \
        -ca-key=/etc/kubernetes/ca/ca-key.pem \
        -config=/etc/kubernetes/ca/ca-config.json \
        -profile=kubernetes etcd-csr.json | cfssljson -bare etcd
# 跟之前类似生成三个文件etcd.csr是个中间证书请求文件，我们最终要的是etcd-key.pem和etcd.pem
ls
etcd.csr  etcd-csr.json  etcd-key.pem  etcd.pem

# 创建工作目录(保存数据的地方)
mkdir -p /var/lib/etcd
# 把etcd服务配置文件copy到系统服务目录
cp ~/kubernetes/kubernetes-starter/target/master-node/etcd.service /lib/systemd/system/
# 创建etcd服务
systemctl enable etcd.service
# 启动etcd服务
service etcd start
# 查看服务日志，看是否有错误信息，确保服务正常
journalctl -f -u etcd.service
# 测试etcd服务是否正常
ETCDCTL_API=3 etcdctl \
  --endpoints=https://192.168.1.72:2379  \
  --cacert=/etc/kubernetes/ca/ca.pem \
  --cert=/etc/kubernetes/ca/etcd/etcd.pem \
  --key=/etc/kubernetes/ca/etcd/etcd-key.pem \
  endpoint health
# 显示以下则为部署成功。
https://192.168.1.72:2379 is healthy: successfully committed proposal: took = 10.408412ms

```

### 1.1.4 部署APIServer

```shell
# 创建存放api证书目录
mkdir -p /etc/kubernetes/ca/kubernetes
# 复制apiserver证书配置
cp ~/kubernetes/kubernetes-starter/target/ca/kubernetes/kubernetes-csr.json /etc/kubernetes/ca/kubernetes/
# 使用根证书(ca.pem)签发kubernetes证书
cd /etc/kubernetes/ca/kubernetes/
cfssl gencert \
        -ca=/etc/kubernetes/ca/ca.pem \
        -ca-key=/etc/kubernetes/ca/ca-key.pem \
        -config=/etc/kubernetes/ca/ca-config.json \
        -profile=kubernetes kubernetes-csr.json | cfssljson -bare kubernetes
# 跟之前类似生成三个文件kubernetes.csr是个中间证书请求文件，我们最终要的是kubernetes-key.pem和kubernetes.pem
ls
kubernetes.csr  kubernetes-csr.json  kubernetes-key.pem  kubernetes.pem

# 生成token认证文件
# 生成随机token
head -c 16 /dev/urandom | od -An -t x | tr -d ' '

root@master:/etc/kubernetes/ca/kubernetes# head -c 16 /dev/urandom | od -An -t x | tr -d ' '
97e8c07dce2b2bab69cfd3162d5383c9
# 写入token.csv文件
echo "97e8c07dce2b2bab69cfd3162d5383c9,kubelet-bootstrap,10001,"system:kubelet-bootstrap"" > /etc/kubernetes/ca/kubernetes/token.csv

# 把apiservice服务配置文件copy到系统服务目录
cp ~/kubernetes/kubernetes-starter/target/master-node/kube-apiserver.service /lib/systemd/system/
# 创建kube-apiserver服务
systemctl enable kube-apiserver.service
# 启动kube-apiserver服务
service kube-apiserver start
# 查看kube-apiserver日志
journalctl -f -u kube-apiserver

# 默认api允许服务端口，可以修改，比如80端口，如果不修改就无法映射
root@master:~/kubernetes/add_node# cat ~/kubernetes/kubernetes-starter/target/master-node/kube-apiserver.service |grep port-range
  --service-node-port-range=20000-40000 \
```

### 1.1.5 部署Controller-manager

> controller-manager一般与api-server在同一台机器上，所以可以使用非安全端口与api-server通讯，不需要生成证书和私钥。

```shell
# 把kube-controller-manager.service 服务配置文件copy到系统服务目录
cp ~/kubernetes/kubernetes-starter/target/master-node/kube-controller-manager.service /lib/systemd/system/
# 创建kube-controller-manager.service 服务
systemctl enable kube-controller-manager.service
# 启动kube-controller-manager.service 服务
service kube-controller-manager start
# 查看kube-controller-manager.service 日志
journalctl -f -u kube-controller-manager
```

### 1.1.6 部署Scheduler

> Scheduler一般与api-server在同一台机器上，所以可以使用非安全端口与api-server通讯，不需要生成证书和私钥。

```shell
# 把scheduler 服务配置文件copy到系统服务目录
cp ~/kubernetes/kubernetes-starter/target/master-node/kube-scheduler.service /lib/systemd/system/
# 创建kube-scheduler.service 服务
systemctl enable kube-scheduler.service
# 启动kube-scheduler.service 服务
service kube-scheduler start
# 查看kube-scheduler.service 日志
journalctl -f -u kube-scheduler
```

### 1.1.7 配置Kubectl管理

```shell
# 创建存放kubectl证书目录
mkdir -p /etc/kubernetes/ca/admin
# 准备admin证书配置 - kubectl只需客户端证书，因此证书请求中 hosts 字段可以为空
# 复制kubectl证书配置
cp ~/kubernetes/kubernetes-starter/target/ca/admin/admin-csr.json /etc/kubernetes/ca/admin/
# 使用根证书(ca.pem)签发admin证书
cd /etc/kubernetes/ca/admin/
cfssl gencert \
        -ca=/etc/kubernetes/ca/ca.pem \
        -ca-key=/etc/kubernetes/ca/ca-key.pem \
        -config=/etc/kubernetes/ca/ca-config.json \
        -profile=kubernetes admin-csr.json | cfssljson -bare admin
# 我们最终要的是admin-key.pem和admin.pem
ls
admin.csr  admin-csr.json  admin-key.pem  admin.pem

# 配置kubectl文件
# 指定apiserver的地址和证书位置
kubectl config set-cluster kubernetes \
        --certificate-authority=/etc/kubernetes/ca/ca.pem \
        --embed-certs=true \
        --server=https://192.168.1.72:6443
# 设置客户端认证参数，指定admin证书和秘钥
kubectl config set-credentials admin \
        --client-certificate=/etc/kubernetes/ca/admin/admin.pem \
        --embed-certs=true \
        --client-key=/etc/kubernetes/ca/admin/admin-key.pem
# 关联用户和集群
kubectl config set-context kubernetes \
        --cluster=kubernetes --user=admin
# 设置当前上下文
kubectl config use-context kubernetes
# 设置结果就是一个配置文件，可以看看内容

cat ~/.kube/config

# 验证master组件
# 以下显示etcd-1、etc-2为Unhealthy是正常的，原因是我们还没有部署etcd-1、etcd-2
root@master:/etc/kubernetes/ca/admin# kubectl get componentstatus
NAME                 STATUS      MESSAGE                                                                                            ERROR
etcd-2               Unhealthy   Get https://192.168.1.74:2379/health: dial tcp 192.168.1.74:2379: getsockopt: connection refused   
controller-manager   Healthy     ok                                                                                                 
etcd-1               Unhealthy   Get https://192.168.1.73:2379/health: dial tcp 192.168.1.73:2379: getsockopt: connection refused   
scheduler            Healthy     ok                                                                                                 
etcd-0               Healthy     {"health": "true"} 

# 创建kubelet-bootstrap绑定
kubectl create clusterrolebinding kubelet-bootstrap --clusterrole=system:node-bootstrapper --user=kubelet-bootstrap
```

### 1.1.8 部署Calico网络

> Calico实现了CNI接口，是kubernetes网络方案的一种选择，它一个纯三层的数据中心网络方案（不需要Overlay），并且与OpenStack、Kubernetes、AWS、GCE等IaaS和容器平台都有良好的集成。 Calico在每一个计算节点利用Linux Kernel实现了一个高效的vRouter来负责数据转发，而每个vRouter通过BGP协议负责把自己上运行的workload的路由信息像整个Calico网络内传播——小规模部署可以直接互联，大规模下可通过指定的BGP route reflector来完成。 这样保证最终所有的workload之间的数据流量都是通过IP路由的方式完成互联的。

```shell
# calico证书用在四个地方：
# calico/node: 这个docker 容器运行时访问 etcd 使用证书
# cni 配置文件中 cni 插件: 需要访问 etcd 使用证书
# calicoctl: 操作集群网络时访问 etcd 使用证书
# calico/kube-controllers: 同步集群网络策略时访问 etcd 使用证书
# 创建存放calico证书
mkdir -p /etc/kubernetes/ca/calico
# 准备calico证书配置 - calico只需客户端证书，因此证书请求中 hosts 字段可以为空
cp ~/kubernetes/kubernetes-starter/target/ca/calico/calico-csr.json /etc/kubernetes/ca/calico/
cd /etc/kubernetes/ca/calico/
cfssl gencert \
        -ca=/etc/kubernetes/ca/ca.pem \
        -ca-key=/etc/kubernetes/ca/ca-key.pem \
        -config=/etc/kubernetes/ca/ca-config.json \
        -profile=kubernetes calico-csr.json | cfssljson -bare calico
# 我们最终要的是calico-key.pem和calico.pem
ls 
calico.csr  calico-csr.json  calico-key.pem  calico.pem
# 启动kube-calico.service 服务
cp ~/kubernetes/kubernetes-starter/target/all-node/kube-calico.service /lib/systemd/system/
systemctl enable kube-calico.service
# 启动kube-calico服务需要下载镜像
service kube-calico start   
journalctl -f -u kube-calico
# 查看节点情况，显示如下内容是因为还没有calico节点，属于正常情况
root@master:/etc/kubernetes/ca/calico# calicoctl node status
Calico process is not running.
```

## 1.2 部署Kubernetes集群Node

> 节点服务器：
>
> hostname:  node1
>
> ip: 192.168.1.72

### 1.2.1 安装Docker

```shell
# 关闭防火墙
ufw disable && ufw status
# 执行docker安装脚本
curl -s  https://raw.githubusercontent.com/jy1779/docker/master/install/aliyun_docker_install.sh | bash
# 获取二进制文件
git clone https://code.aliyun.com/jy1779/kubernetes.git	
# 解压kubernetes-bins,添加到环境变量
tar xf ./kubernetes/kubernetes-bins.tar.gz -C /usr/local/sbin/
echo 'export PATH=$PATH:/usr/local/sbin/kubernetes-bins' >> /etc/profile && source /etc/profile
# 修改docker.server
LINE=$(grep -n ExecStart /lib/systemd/system/docker.service|awk -F : '{print $1}')
EXECSTARTPOST='ExecStartPost=/sbin/iptables -I FORWARD -s 0.0.0.0/0 -j ACCEPT'
sed "$LINE a$EXECSTARTPOST" -i /lib/systemd/system/docker.service
# 重启docker
systemctl daemon-reload && service docker restart

```

### 1.2.2 生成配置文件

```shell
# 添加内核参数

cat <<EOF > /etc/sysctl.d/k8s.conf
net.ipv4.ip_forward = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
EOF

# 使内核参数生效
sysctl -p /etc/sysctl.d/k8s.conf

# 修改配置文件config.properties
root@node01:~# cd /root/kubernetes/kubernetes-starter/
root@node01:~/kubernetes/kubernetes-starter# cat config.properties 
#kubernetes二进制文件目录,eg: /home/michael/bin
BIN_PATH=/usr/local/sbin/kubernetes-bins

#当前节点ip, eg: 192.168.1.102
NODE_IP=192.168.1.73

#etcd服务集群列表, eg: http://192.168.1.102:2379
#如果已有etcd集群可以填写现有的。没有的话填写：http://${MASTER_IP}:2379 （MASTER_IP自行替换成自己的主节点ip）
ETCD_ENDPOINTS=https://192.168.1.72:2379,https://192.168.1.73:2379,https://192.168.1.74:2379

#kubernetes主节点ip地址, eg: 192.168.1.102
MASTER_IP=192.168.1.72
# 生成配置文件
cd ~/kubernetes/kubernetes-starter && ./gen-config.sh with-ca

# 安装cfssl
wget -q --show-progress --https-only --timestamping \
  https://pkg.cfssl.org/R1.2/cfssl_linux-amd64 \
  https://pkg.cfssl.org/R1.2/cfssljson_linux-amd64
chmod +x cfssl_linux-amd64 cfssljson_linux-amd64
mv cfssl_linux-amd64 /usr/local/bin/cfssl
mv cfssljson_linux-amd64 /usr/local/bin/cfssljson
cfssl version

# 创建存放证书目录
mkdir -p /etc/kubernetes/ca/
# 从master获取calico证书
rsync -av 192.168.1.72:/etc/kubernetes/ca/ca* /etc/kubernetes/ca/

```

### 1.2.3 部署Calico网络

```shell
# 复制calico启动文件到系统服务目录
cp ~/kubernetes/kubernetes-starter/target/all-node/kube-calico.service /lib/systemd/system/
# 创建kube-calico.service
systemctl enable kube-calico.service
# 启动kube-calico.service 服务
service kube-calico start
# 查看calico节点，可以看到master节点的calico
calicoctl node status
IPv4 BGP status
+--------------+-------------------+-------+----------+-------------+
| PEER ADDRESS |     PEER TYPE     | STATE |  SINCE   |    INFO     |
+--------------+-------------------+-------+----------+-------------+
| 192.168.1.72 | node-to-node mesh | up    | 09:03:00 | Established |
+--------------+-------------------+-------+----------+-------------+

```

### 1.2.4 部署Kubelet

```shell
cd /etc/kubernetes/

# 创建bootstrap.kubeconfig
kubectl config set-cluster kubernetes \
        --certificate-authority=/etc/kubernetes/ca/ca.pem \
        --embed-certs=true \
        --server=https://192.168.1.72:6443 \
        --kubeconfig=bootstrap.kubeconfig
kubectl config set-credentials kubelet-bootstrap \
        --token=97e8c07dce2b2bab69cfd3162d5383c9 \
        --kubeconfig=bootstrap.kubeconfig
kubectl config set-context default \
        --cluster=kubernetes \
        --user=kubelet-bootstrap \
        --kubeconfig=bootstrap.kubeconfig
kubectl config use-context default --kubeconfig=bootstrap.kubeconfig

# 准备cni
mkdir -p /etc/cni/net.d/
cp ~/kubernetes/kubernetes-starter/target/worker-node/10-calico.conf /etc/cni/net.d/

# 创建存放kubelet工作目录
mkdir /var/lib/kubelet
# 将kubelet.service 复制到系统目录
cp ~/kubernetes/kubernetes-starter/target/worker-node/kubelet.service /lib/systemd/system/
# 创建kubelet服务
systemctl enable kubelet
# 启动kubelet服务
service kubelet start

```

### 1.2.5 Master签发证书

```shell
# 在master服务器执行
# 查看csr
kubectl get csr
NAME                                                   AGE       REQUESTOR           CONDITION
node-csr-xNqwjv6k56NdkqbEpoinSOKEekPXrMvI6EgUGzTrngk   1m        kubelet-bootstrap   Pending
# 允许请求
kubectl get csr|grep 'Pending' | awk '{print $1}'| xargs kubectl certificate approve

certificatesigningrequest "node-csr-xNqwjv6k56NdkqbEpoinSOKEekPXrMvI6EgUGzTrngk" approved
# 再次查看 kubectl get csr
NAME                                                   AGE       REQUESTOR           CONDITION
node-csr-xNqwjv6k56NdkqbEpoinSOKEekPXrMvI6EgUGzTrngk   1m        kubelet-bootstrap   Approved,Issued
# 验证节点
root@master:/etc/kubernetes/ca/calico# kubectl get node
NAME           STATUS    ROLES     AGE       VERSION
192.168.1.73   Ready     <none>    24s       v1.9.0
```

### 1.2.6 部署kube-proxy

```shell
# 创建kube-proxy工作目录及存放证书目录
mkdir -p /var/lib/kube-proxy
mkdir -p /etc/kubernetes/ca/kube-proxy
# 复制kube-proxy服务配置文件
cp ~/kubernetes/kubernetes-starter/target/ca/kube-proxy/kube-proxy-csr.json /etc/kubernetes/ca/kube-proxy/

cd /etc/kubernetes/ca/kube-proxy/
# 使用根证书(ca.pem)签发calico证书

cfssl gencert \
        -ca=/etc/kubernetes/ca/ca.pem \
        -ca-key=/etc/kubernetes/ca/ca-key.pem \
        -config=/etc/kubernetes/ca/ca-config.json \
        -profile=kubernetes kube-proxy-csr.json | cfssljson -bare kube-proxy
cd /etc/kubernetes/
kubectl config set-cluster kubernetes \
        --certificate-authority=/etc/kubernetes/ca/ca.pem \
        --embed-certs=true \
        --server=https://192.168.1.72:6443 \
        --kubeconfig=kube-proxy.kubeconfig
kubectl config set-credentials kube-proxy \
        --client-certificate=/etc/kubernetes/ca/kube-proxy/kube-proxy.pem \
        --client-key=/etc/kubernetes/ca/kube-proxy/kube-proxy-key.pem \
        --embed-certs=true \
        --kubeconfig=kube-proxy.kubeconfig
kubectl config set-context default \
        --cluster=kubernetes \
        --user=kube-proxy \
        --kubeconfig=kube-proxy.kubeconfig
kubectl config use-context default --kubeconfig=kube-proxy.kubeconfig

# 复制kube-proxy启动文件到系统目录
cp ~/kubernetes/kubernetes-starter/target/worker-node/kube-proxy.service /lib/systemd/system/
# 创建kube-proxy服务
systemctl enable kube-proxy
# 启动kube-proxy服务
service kube-proxy start
# 创建pods,验证kube-proxy
root@master:~/kubernetes/service# cat nginx-deployment.yaml 
apiVersion: apps/v1beta1
kind: Deployment
metadata:
  name: nginx
  annotations:
    nginx.ingress.kubernetes.io/secure-backends: "true"
spec:
  replicas: 1
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: registry.cn-hangzhou.aliyuncs.com/jonny/nginx:1.9.14
        ports:
          - containerPort: 80
root@master:~/kubernetes/service# kubectl apply -f nginx-deployment.yaml 
root@master:~/kubernetes/service# kubectl get pods
NAME                     READY     STATUS    RESTARTS   AGE
nginx-65dbdf6899-x52ws   1/1       Running   0          2m

root@master:~/kubernetes/service# cat nginx-service.yaml 
apiVersion: v1
kind: Service
metadata:
  name: nginx-service
spec:
  selector:
    app: nginx
  ports:
  - protocol: TCP
    port: 80
    targetPort: 80
root@master:~/kubernetes/service# kubectl get service
NAME            TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)   AGE
kubernetes      ClusterIP   10.68.0.1       <none>        443/TCP   4h
nginx-service   ClusterIP   10.68.142.199   <none>        80/TCP    3m

# 进入容器验证，访问ClusterIP
bash-4.3# curl -I 10.68.142.199
HTTP/1.1 200 OK
Server: nginx/1.9.14
Date: Wed, 17 Oct 2018 06:47:52 GMT
Content-Type: text/html
Content-Length: 612
Last-Modified: Wed, 21 Sep 2016 08:11:20 GMT
Connection: keep-alive
ETag: "57e240a8-264"
Accept-Ranges: bytes

# 在节点上验证
root@node01:/etc/kubernetes# curl -I 10.68.142.199
HTTP/1.1 200 OK
Server: nginx/1.9.14
Date: Wed, 17 Oct 2018 06:48:38 GMT
Content-Type: text/html
Content-Length: 612
Last-Modified: Wed, 21 Sep 2016 08:11:20 GMT
Connection: keep-alive
ETag: "57e240a8-264"
Accept-Ranges: bytes

```

## 1.3 部署Kube-dns

### 1.3.1 创建Kube-dns服务

```shell
cd /root/kubernetes/kubernetes-starter/target/services/
cat kube-dns.yaml
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: kube-dns
  namespace: kube-system
  labels:
    addonmanager.kubernetes.io/mode: EnsureExists

---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: kube-dns
  namespace: kube-system
  labels:
    addonmanager.kubernetes.io/mode: Reconcile

---
apiVersion: v1
kind: Service
metadata:
  name: kube-dns
  namespace: kube-system
  labels:
    k8s-app: kube-dns
    addonmanager.kubernetes.io/mode: Reconcile
    kubernetes.io/name: "KubeDNS"
spec:
  selector:
    k8s-app: kube-dns
  clusterIP: 10.68.0.2
  ports:
  - name: dns
    port: 53
    protocol: UDP
  - name: dns-tcp
    port: 53
    protocol: TCP

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kube-dns
  namespace: kube-system
  labels:
    k8s-app: kube-dns
    addonmanager.kubernetes.io/mode: Reconcile
spec:
  strategy:
    rollingUpdate:
      maxSurge: 10%
      maxUnavailable: 0
  selector:
    matchLabels:
      k8s-app: kube-dns
  template:
    metadata:
      labels:
        k8s-app: kube-dns
      annotations:
        scheduler.alpha.kubernetes.io/critical-pod: ''
    spec:
      tolerations:
      - key: "CriticalAddonsOnly"
        operator: "Exists"
      volumes:
      - name: kube-dns-config
        configMap:
          name: kube-dns
          optional: true
      containers:
      - name: kubedns
        image: registry.cn-hangzhou.aliyuncs.com/imooc/k8s-dns-kube-dns-amd64:1.14.5
        resources:
          # TODO: Set memory limits when we've profiled the container for large
          # clusters, then set request = limit to keep this container in
          # guaranteed class. Currently, this container falls into the
          # "burstable" category so the kubelet doesn't backoff from restarting it.
          limits:
            memory: 170Mi
          requests:
            cpu: 100m
            memory: 70Mi
        livenessProbe:
          httpGet:
            path: /healthcheck/kubedns
            port: 10054
            scheme: HTTP
          initialDelaySeconds: 60
          timeoutSeconds: 5
          successThreshold: 1
          failureThreshold: 5
        readinessProbe:
          httpGet:
            path: /readiness
            port: 8081
            scheme: HTTP
          # we poll on pod startup for the Kubernetes master service and
          # only setup the /readiness HTTP server once that's available.
          initialDelaySeconds: 3
          timeoutSeconds: 5
        args:
        - --domain=cluster.local.
        - --dns-port=10053
        - --config-dir=/kube-dns-config
        - --v=2
        env:
        - name: PROMETHEUS_PORT
          value: "10055"
        ports:
        - containerPort: 10053
          name: dns-local
          protocol: UDP
        - containerPort: 10053
          name: dns-tcp-local
          protocol: TCP
        - containerPort: 10055
          name: metrics
          protocol: TCP
        volumeMounts:
        - name: kube-dns-config
          mountPath: /kube-dns-config
      - name: dnsmasq
        image: registry.cn-hangzhou.aliyuncs.com/imooc/k8s-dns-dnsmasq-nanny-amd64:1.14.5
        livenessProbe:
          httpGet:
            path: /healthcheck/dnsmasq
            port: 10054
            scheme: HTTP
          initialDelaySeconds: 60
          timeoutSeconds: 5
          successThreshold: 1
          failureThreshold: 5
        args:
        - -v=2
        - -logtostderr
        - -configDir=/etc/k8s/dns/dnsmasq-nanny
        - -restartDnsmasq=true
        - --
        - -k
        - --cache-size=1000
        - --log-facility=-
        - --server=/cluster.local./127.0.0.1#10053
        - --server=/in-addr.arpa/127.0.0.1#10053
        - --server=/ip6.arpa/127.0.0.1#10053
        ports:
        - containerPort: 53
          name: dns
          protocol: UDP
        - containerPort: 53
          name: dns-tcp
          protocol: TCP
        # see: https://github.com/kubernetes/kubernetes/issues/29055 for details
        resources:
          requests:
            cpu: 150m
            memory: 20Mi
        volumeMounts:
        - name: kube-dns-config
          mountPath: /etc/k8s/dns/dnsmasq-nanny
      - name: sidecar
        image: registry.cn-hangzhou.aliyuncs.com/imooc/k8s-dns-sidecar-amd64:1.14.5
        livenessProbe:
          httpGet:
            path: /metrics
            port: 10054
            scheme: HTTP
          initialDelaySeconds: 60
          timeoutSeconds: 5
          successThreshold: 1
          failureThreshold: 5
        args:
        - --v=2
        - --logtostderr
        - --probe=kubedns,127.0.0.1:10053,kubernetes.default.svc.cluster.local.,5,A
        - --probe=dnsmasq,127.0.0.1:53,kubernetes.default.svc.cluster.local.,5,A
        ports:
        - containerPort: 10054
          name: metrics
          protocol: TCP
        resources:
          requests:
            memory: 20Mi
            cpu: 10m
      dnsPolicy: Default  # Don't use cluster DNS.
      serviceAccountName: kube-dns
      
root@master:~/kubernetes/kubernetes-starter/target/services# kubectl apply -f kube-dns.yaml
root@master:~/kubernetes/kubernetes-starter/target/services# kubectl -n kube-system get pods
NAME                        READY     STATUS    RESTARTS   AGE
kube-dns-565c8d55b4-72dhw   3/3       Running   0          1m

```

### 1.3.2 验证Kube-dns

```shell
root@master:~/kubernetes/kubernetes-starter/target/services# kubectl get pods
NAME                     READY     STATUS    RESTARTS   AGE
nginx-65dbdf6899-x52ws   1/1       Running   0          14m
root@master:~/kubernetes/kubernetes-starter/target/services# kubectl get service
NAME            TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)   AGE
kubernetes      ClusterIP   10.68.0.1       <none>        443/TCP   4h
nginx-service   ClusterIP   10.68.142.199   <none>        80/TCP    13m
root@master:~# kubectl exec -it nginx-65dbdf6899-x52ws bash
bash-4.3# nslookup nginx-service
nslookup: can't resolve '(null)': Name does not resolve

Name:      nginx-service
Address 1: 10.68.142.199 nginx-service.default.svc.cluster.local
bash-4.3# curl -I  nginx-service  #使用服务名访问
HTTP/1.1 200 OK
Server: nginx/1.9.14
Date: Wed, 17 Oct 2018 06:56:43 GMT
Content-Type: text/html
Content-Length: 612
Last-Modified: Wed, 21 Sep 2016 08:11:20 GMT
Connection: keep-alive
ETag: "57e240a8-264"
Accept-Ranges: bytes

```

## 1.4 部署Dashboard

### 1.4.1 创建Dashboard服务

```shell
root@master:~/kubernetes/kubernetes-starter/target/services# cat kube-dashboard.yaml
# Copyright 2017 The Kubernetes Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Configuration to deploy release version of the Dashboard UI compatible with
# Kubernetes 1.8.
#
# Example usage: kubectl create -f <this_file>

# ------------------- Dashboard Secret ------------------- #

apiVersion: v1
kind: Secret
metadata:
  labels:
    k8s-app: kubernetes-dashboard
  name: kubernetes-dashboard-certs
  namespace: kube-system
type: Opaque

---
# ------------------- Dashboard Service Account ------------------- #

apiVersion: v1
kind: ServiceAccount
metadata:
  labels:
    k8s-app: kubernetes-dashboard
  name: kubernetes-dashboard
  namespace: kube-system

---
# ------------------- Dashboard Role & Role Binding ------------------- #

kind: Role
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: kubernetes-dashboard-minimal
  namespace: kube-system
rules:
  # Allow Dashboard to create 'kubernetes-dashboard-key-holder' secret.
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["create"]
  # Allow Dashboard to create 'kubernetes-dashboard-settings' config map.
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["create"]
  # Allow Dashboard to get, update and delete Dashboard exclusive secrets.
- apiGroups: [""]
  resources: ["secrets"]
  resourceNames: ["kubernetes-dashboard-key-holder", "kubernetes-dashboard-certs"]
  verbs: ["get", "update", "delete"]
  # Allow Dashboard to get and update 'kubernetes-dashboard-settings' config map.
- apiGroups: [""]
  resources: ["configmaps"]
  resourceNames: ["kubernetes-dashboard-settings"]
  verbs: ["get", "update"]
  # Allow Dashboard to get metrics from heapster.
- apiGroups: [""]
  resources: ["services"]
  resourceNames: ["heapster"]
  verbs: ["proxy"]
- apiGroups: [""]
  resources: ["services/proxy"]
  resourceNames: ["heapster", "http:heapster:", "https:heapster:"]
  verbs: ["get"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: kubernetes-dashboard-minimal
  namespace: kube-system
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: kubernetes-dashboard-minimal
subjects:
- kind: ServiceAccount
  name: kubernetes-dashboard
  namespace: kube-system

---
# ------------------- Dashboard Deployment ------------------- #

kind: Deployment
apiVersion: apps/v1beta2
metadata:
  labels:
    k8s-app: kubernetes-dashboard
  name: kubernetes-dashboard
  namespace: kube-system
spec:
  replicas: 1
  revisionHistoryLimit: 10
  selector:
    matchLabels:
      k8s-app: kubernetes-dashboard
  template:
    metadata:
      labels:
        k8s-app: kubernetes-dashboard
    spec:
      containers:
      - name: kubernetes-dashboard
        image: registry.cn-hangzhou.aliyuncs.com/jonny/kubernetes-dashboard-amd64:v1.8.1
        ports:
        - containerPort: 8443
          protocol: TCP
        args:
          - --auto-generate-certificates
          # Uncomment the following line to manually specify Kubernetes API server Host
          # If not specified, Dashboard will attempt to auto discover the API server and connect
          # to it. Uncomment only if the default does not work.
          # - --apiserver-host=http://my-address:port
        volumeMounts:
        - name: kubernetes-dashboard-certs
          mountPath: /certs
          # Create on-disk volume to store exec logs
        - mountPath: /tmp
          name: tmp-volume
        livenessProbe:
          httpGet:
            scheme: HTTPS
            path: /
            port: 8443
          initialDelaySeconds: 30
          timeoutSeconds: 30
      volumes:
      - name: kubernetes-dashboard-certs
        secret:
          secretName: kubernetes-dashboard-certs
      - name: tmp-volume
        emptyDir: {}
      serviceAccountName: kubernetes-dashboard
      # Comment the following tolerations if Dashboard must not be deployed on master
      tolerations:
      - key: node-role.kubernetes.io/master
        effect: NoSchedule

---
# ------------------- Dashboard Service ------------------- #

kind: Service
apiVersion: v1
metadata:
  labels:
    k8s-app: kubernetes-dashboard
  name: kubernetes-dashboard
  namespace: kube-system
spec:
  ports:
    - port: 443
      targetPort: 8443
      nodePort: 9443
  selector:
    k8s-app: kubernetes-dashboard
  type: NodePort
#查看pod
root@master:~/kubernetes/kubernetes-starter/target/services# kubectl -n kube-system get pods
NAME                                   READY     STATUS    RESTARTS   AGE
kube-dns-565c8d55b4-72dhw              3/3       Running   0          12m
kubernetes-dashboard-c6fdc9bcb-p6kvb   1/1       Running   0          1m
#查看service NodePort暴露了9443端口，可以使用该端口访问dashboard
root@master:~/kubernetes/kubernetes-starter/target/services# kubectl -n kube-system get service
NAME                   TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)         AGE
kube-dns               ClusterIP   10.68.0.2      <none>        53/UDP,53/TCP   12m
kubernetes-dashboard   NodePort    10.68.214.34   <none>        443:9443/TCP    1m
root@master:~/kubernetes/kubernetes-starter/target/services# kubectl apply -f kube-dashboard.yaml 
secret "kubernetes-dashboard-certs" created
serviceaccount "kubernetes-dashboard" created
role "kubernetes-dashboard-minimal" created
rolebinding "kubernetes-dashboard-minimal" created
deployment "kubernetes-dashboard" created
service "kubernetes-dashboard" created
```

### 1.4.2 验证访问Dashboard

```shell
root@master:~/kubernetes/role# cat admin-role.yaml
kind: ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1beta1
metadata:
  name: admin
  annotations:
    rbac.authorization.kubernetes.io/autoupdate: "true"
roleRef:
  kind: ClusterRole
  name: cluster-admin
  apiGroup: rbac.authorization.k8s.io
subjects:
- kind: ServiceAccount
  name: admin
  namespace: kube-system
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: admin
  namespace: kube-system
  labels:
    kubernetes.io/cluster-service: "true"
    addonmanager.kubernetes.io/mode: Reconcile
# 创建绑定admin
root@master:~/kubernetes/role# kubectl apply -f admin-role.yaml 
clusterrolebinding "admin" created
serviceaccount "admin" created
# 查看secret
root@master:~/kubernetes/role# kubectl -n kube-system get secret |grep admin
admin-token-8dmvq                  kubernetes.io/service-account-token   3         1m
# 查看token,使用该token登录dashboard
root@master:~/kubernetes/role# kubectl -n kube-system  get secret admin-token-8dmvq -o jsonpath={.data.token}| base64 -d
eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJrdWJlLXN5c3RlbSIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VjcmV0Lm5hbWUiOiJhZG1pbi10b2tlbi04ZG12cSIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50Lm5hbWUiOiJhZG1pbiIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50LnVpZCI6IjkxMjM2Njg2LWQxZGItMTFlOC05YTU5LTAwMGMyOTYzYWFjYyIsInN1YiI6InN5c3RlbTpzZXJ2aWNlYWNjb3VudDprdWJlLXN5c3RlbTphZG1pbiJ9.YUTw4l8GsntcXsj467V9SWnwhX1JTrkGDNdQYd1OPJQ8IeQBghe43UKSFoFe-a1nmfTyOaMueXMdIUJXbsE1w7Byb21InpKmGNmwR0_KxLmydNVIA11hm062Apvt-Zf-ky0GOBNtM3_APvfmXSZuYV_5ZNC0PvHObF-azlSwcGtsCUUT-Zs2PuvPSh8OAbk2EBBvVDReOU-rNkL3vOiekb4Rjah1AE6bCbp7R4PSOv9_1BqCteLCxrEyE7G1c0D0wo5J3k3Ur_XZ0bW6SBU77RyZEx-8fzHQcQd1LObHfhsuRQRAR8pDyyn3g977h3seM4L2DLtQ-J0EhqGBtaycDw
# 也可以使用这种方法
root@master:~/kubernetes/role# kubectl -n kube-system describe secret admin-token-8dmvq
Name:         admin-token-8dmvq
Namespace:    kube-system
Labels:       <none>
Annotations:  kubernetes.io/service-account.name=admin
              kubernetes.io/service-account.uid=91236686-d1db-11e8-9a59-000c2963aacc

Type:  kubernetes.io/service-account-token

Data
====
ca.crt:     1346 bytes
namespace:  11 bytes
token:      eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJrdWJlLXN5c3RlbSIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VjcmV0Lm5hbWUiOiJhZG1pbi10b2tlbi04ZG12cSIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50Lm5hbWUiOiJhZG1pbiIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50LnVpZCI6IjkxMjM2Njg2LWQxZGItMTFlOC05YTU5LTAwMGMyOTYzYWFjYyIsInN1YiI6InN5c3RlbTpzZXJ2aWNlYWNjb3VudDprdWJlLXN5c3RlbTphZG1pbiJ9.YUTw4l8GsntcXsj467V9SWnwhX1JTrkGDNdQYd1OPJQ8IeQBghe43UKSFoFe-a1nmfTyOaMueXMdIUJXbsE1w7Byb21InpKmGNmwR0_KxLmydNVIA11hm062Apvt-Zf-ky0GOBNtM3_APvfmXSZuYV_5ZNC0PvHObF-azlSwcGtsCUUT-Zs2PuvPSh8OAbk2EBBvVDReOU-rNkL3vOiekb4Rjah1AE6bCbp7R4PSOv9_1BqCteLCxrEyE7G1c0D0wo5J3k3Ur_XZ0bW6SBU77RyZEx-8fzHQcQd1LObHfhsuRQRAR8pDyyn3g977h3seM4L2DLtQ-J0EhqGBtaycDw

```

访问URL：https://192.168.1.73:9443/ 复制上面的token，选择令牌登录，下图：

![](https://raw.githubusercontent.com/jy1779/doc/master/image/kubernetes/dashboard_login.png)

![](https://raw.githubusercontent.com/jy1779/doc/master/image/kubernetes/dashboard.png)

## 1.5 部署etcd集群

> 前面部署k8s集群，在生成配置文件的步骤中，修改config.properties文件里的ETCD_ENDPOINTS变量设置3个etcd节点，但是我们只在master部署了一个etcd节点，如下：
>
> ```shell
> root@master:~# cat  /root/kubernetes/kubernetes-starter/config.properties |grep ETCD_ENDPOINTS
> ETCD_ENDPOINTS=https://192.168.1.72:2379,https://192.168.1.73:2379,https://192.168.1.74:2379
> ```
>
> 在部署完k8s集群后，查看componentstatus情况也显示etcd-1、etcd-2不健康
>
> ```shell
> root@master:~# kubectl get componentstatus|grep Unhealthy
> etcd-2               Unhealthy   Get https://192.168.1.74:2379/health: dial tcp 192.168.1.74:2379: getsockopt: connection refused   
> etcd-1               Unhealthy   Get https://192.168.1.73:2379/health: dial tcp 192.168.1.73:2379: getsockopt: connection refused
> ```

### 1.5.1 修改etcd为集群

```shell
# 修改etcd服务启动文件，添加三个参数
--initial-cluster #初始化集群节点
--initial-cluster-state #初始化集群状态：('new' or 'existing') 
--initial-cluster-token #初始化集群token
root@master:~# cat  /lib/systemd/system/etcd.service 
[Unit]
Description=Etcd Server
After=network.target
After=network-online.target
Wants=network-online.target
Documentation=https://github.com/coreos

[Service]
Type=notify
WorkingDirectory=/var/lib/etcd/
ExecStart=/usr/local/sbin/kubernetes-bins/etcd \
  --name=192.168.1.72 \
  --listen-client-urls=https://192.168.1.72:2379,http://127.0.0.1:2379 \
  --advertise-client-urls=https://192.168.1.72:2379 \
  --data-dir=/var/lib/etcd \
  --listen-peer-urls=https://192.168.1.72:2380 \
  --initial-advertise-peer-urls=https://192.168.1.72:2380 \
  --initial-cluster=192.168.1.72=https://192.168.1.72:2380 \ 
  --initial-cluster-state=new \
  --initial-cluster-token=etcd-cluster \
  --cert-file=/etc/kubernetes/ca/etcd/etcd.pem \
  --key-file=/etc/kubernetes/ca/etcd/etcd-key.pem \
  --peer-cert-file=/etc/kubernetes/ca/etcd/etcd.pem \
  --peer-key-file=/etc/kubernetes/ca/etcd/etcd-key.pem \
  --trusted-ca-file=/etc/kubernetes/ca/ca.pem \
  --peer-trusted-ca-file=/etc/kubernetes/ca/ca.pem
Restart=on-failure
RestartSec=5
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
root@master:~# systemctl daemon-reload #重载etcd服务启动文件
root@master:~# service etcd restart #重启etcd服务

```

### 1.5.2 添加etcd集群节点

```shell
# 查看etcd节点，目前只有192.168.1.72一个节点
root@master:~# ETCDCTL_API=3 etcdctl   --endpoints=https://192.168.1.72:2379   --cacert=/etc/kubernetes/ca/ca.pem   --cert=/etc/kubernetes/ca/etcd/etcd.pem   --key=/etc/kubernetes/ca/etcd/etcd-key.pem   member list
5c81b5ea448e2eb, started, 192.168.1.72, https://192.168.1.72:2380, https://192.168.1.72:2379

# 添加etcd节点：192.168.1.73
root@master:~# ETCDCTL_API=3 etcdctl --endpoints=https://192.168.1.72:2379 --cacert=/etc/kubernetes/ca/ca.pem --cert=/etc/kubernetes/ca/etcd/etcd.pem --key=/etc/kubernetes/ca/etcd/etcd-key.pem member add 192.168.1.73 --peer-urls=https://192.168.1.73:2380
Member  d584359b169648b added to cluster  5867db71109a61d
# 添加etcd节点后，出现以下三个变量，将三个变量写入etcd节点的启动配置文件
ETCD_NAME="192.168.1.73"
ETCD_INITIAL_CLUSTER="192.168.1.72=https://192.168.1.72:2380,192.168.1.73=https://192.168.1.73:2380"
ETCD_INITIAL_CLUSTER_STATE="existing"
```

### 1.5.3 部署etcd节点

```shell
# 创建存放etcd证书的目录
mkdir -p /etc/kubernetes/ca/etcd
# 复制etcd证书配置
cp ~/kubernetes/kubernetes-starter/target/ca/etcd/etcd-csr.json /etc/kubernetes/ca/etcd/
cd /etc/kubernetes/ca/etcd/
# 使用根证书(ca.pem)签发etcd证书
cfssl gencert \
        -ca=/etc/kubernetes/ca/ca.pem \
        -ca-key=/etc/kubernetes/ca/ca-key.pem \
        -config=/etc/kubernetes/ca/ca-config.json \
        -profile=kubernetes etcd-csr.json | cfssljson -bare etcd
# 跟之前类似生成三个文件etcd.csr是个中间证书请求文件，我们最终要的是etcd-key.pem和etcd.pem
ls
etcd.csr  etcd-csr.json  etcd-key.pem  etcd.pem
# 创建工作目录(保存数据的地方)
mkdir -p /var/lib/etcd
# 把etcd服务配置文件copy到系统服务目录
cp ~/kubernetes/kubernetes-starter/target/master-node/etcd.service /lib/systemd/system/
# 新增集群参数
--name=192.168.1.73 # name默认在生成配置文件的时候已经生成好，所以不需要添加
--initial-cluster=192.168.1.72=https://192.168.1.72:2380,192.168.1.73=https://192.168.1.73:2380
--initial-cluster-state=existing
--initial-cluster-token=etcd-cluster
root@node01:~# cat /lib/systemd/system/etcd.service 
[Unit]
Description=Etcd Server
After=network.target
After=network-online.target
Wants=network-online.target
Documentation=https://github.com/coreos

[Service]
Type=notify
WorkingDirectory=/var/lib/etcd/
ExecStart=/usr/local/sbin/kubernetes-bins/etcd \
  --name=192.168.1.73 \
  --listen-client-urls=https://192.168.1.73:2379,http://127.0.0.1:2379 \
  --advertise-client-urls=https://192.168.1.73:2379 \
  --data-dir=/var/lib/etcd \
  --listen-peer-urls=https://192.168.1.73:2380 \
  --initial-advertise-peer-urls=https://192.168.1.73:2380 \
  --initial-cluster=192.168.1.72=https://192.168.1.72:2380,192.168.1.73=https://192.168.1.73:2380 \
  --initial-cluster-state=existing \
  --initial-cluster-token=etcd-cluster \
  --cert-file=/etc/kubernetes/ca/etcd/etcd.pem \
  --key-file=/etc/kubernetes/ca/etcd/etcd-key.pem \
  --peer-cert-file=/etc/kubernetes/ca/etcd/etcd.pem \
  --peer-key-file=/etc/kubernetes/ca/etcd/etcd-key.pem \
  --trusted-ca-file=/etc/kubernetes/ca/ca.pem \
  --peer-trusted-ca-file=/etc/kubernetes/ca/ca.pem
Restart=on-failure
RestartSec=5
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
# 创建etcd服务
systemctl enable etcd.service
# 启动etcd服务
service etcd start
```

### 1.5.4 验证etcd节点

```shell
# 查看集群节点
root@master:~# ETCDCTL_API=3 etcdctl   --endpoints=https://192.168.1.72:2379   --cacert=/etc/kubernetes/ca/ca.pem   --cert=/etc/kubernetes/ca/etcd/etcd.pem   --key=/etc/kubernetes/ca/etcd/etcd-key.pem   member list
5c81b5ea448e2eb, started, 192.168.1.72, https://192.168.1.72:2380, https://192.168.1.72:2379
d584359b169648b, started, 192.168.1.73, https://192.168.1.73:2380, https://192.168.1.73:2379
# 查看componentstatus情况，etcd-1已经健康
root@master:~# kubectl get componentstatus
NAME                 STATUS      MESSAGE                                                                                            ERROR
etcd-2               Unhealthy   Get https://192.168.1.74:2379/health: dial tcp 192.168.1.74:2379: getsockopt: connection refused   
controller-manager   Healthy     ok                                                                                                 
scheduler            Healthy     ok                                                                                                 
etcd-1               Healthy     {"health": "true"}                                                                                 
etcd-0               Healthy     {"health": "true"}  
# 查看k8s集群数据是否同步
ETCDCTL_API=3 etcdctl   --endpoints=https://192.168.1.73:2379  --cacert=/etc/kubernetes/ca/ca.pem   --cert=/etc/kubernetes/ca/etcd/etcd.pem   --key=/etc/kubernetes/ca/etcd/etcd-key.pem get / --prefix --keys-only
# etcd-2 同样以这样的方式添加
```

## 1.6 kubernetes集群添加Node(脚本)

1. 在master服务器上操作

2. master与node节点做免密登录

3. 准备执行shell命令的脚本，路径：/scripts/python/shell.py

4. 准备添加node脚本，路径：/root/kubernetes/add_node/add_node.py

5. 创建目录：/root/kubernetes/add_node，准备以下条件：

   ```shell
   root@master:~/kubernetes# tree add_node/
   add_node/
   ├── add_node.py   # 新增node脚本,授权可执行权限
   ├── bootstrap.kubeconfig # 在现有节点拷贝bootstrap.kubeconfig
   ├── config.properties    # 准备config.properties
   ├── kube-proxy           # 在现有节点拷贝kube-proxy证书
   │   ├── kube-proxy.csr
   │   ├── kube-proxy-csr.json
   │   ├── kube-proxy-key.pem
   │   └── kube-proxy.pem
   └── kube-proxy.kubeconfig # 在现有节点拷贝kube-proxy.kubeconfig
   
   ```

6. 实际操作

   ```shell
   # 创建执行shell脚本目录
   root@master:~# mkdir -p /scripts/python/
   # 创建shell.py文件
   root@master:~# touch /scripts/python/shell.py
   # shell.py脚本内容
   root@master:~# cat /scripts/python/shell.py 
   #!/usr/bin/env python3
   # -*- coding: utf-8 -*-
   import subprocess
   import paramiko
   import re
   import sys
   class Cmd(object):
       def onetime_shell(self,cmd):
           cmd = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
           cmd = cmd.communicate()
           cmd = cmd[0].decode().rstrip()
           return cmd
       def realtime_shell(self,cmd):
           cmd = subprocess.call(cmd, shell=True)
           return cmd
   class Remote_cmd(object):
       def __init__(self,PrivateKey,IP,Port,User):
           self.private_key = paramiko.RSAKey.from_private_key_file(PrivateKey)
           self.ssh = paramiko.SSHClient()
           self.set_missing_host_key_policy = self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
           self.connect = self.ssh.connect(hostname=IP, port=Port, username=User,pkey=self.private_key)
       def onetime_shell(self,cmd,notice=False):
           stdin, stdout, stderr = self.ssh.exec_command(cmd)
           result = stdout.read().decode('utf-8').rstrip()
           if notice:
              self.ssh.close()
           return result
           
       def realtime_shell(self,cmd,notice=False):
           try:
              stdin, stdout, stderr = self.ssh.exec_command(cmd)
              for line in stdout:
                  print(line.strip("\n"))
              for error in stderr:
                  print(error.strip("\n"))
              if notice:
                 self.ssh.close()
           except Exception as e:
              print("execute command %s error, error message is %s" % (cmd, e))
              return ""
   # 安装paramiko
   root@master:~# apt-get install  python3-pip libevent-dev libffi-dev libssl-dev -y
   root@master:~# pip3 install paramiko -i https://pypi.mirrors.ustc.edu.cn/simple/  --trusted-host https://pypi.mirrors.ustc.edu.cn
   # 创建目录存放需要的文件
   root@master:~# mkdir /root/kubernetes/add_node
   # 进入目录，执行下面指令获取需要的文件
   root@master:~# cd /root/kubernetes/add_node/
   # 从现在有node01节点获取bootstrap.kubeconfig
   root@master:~/kubernetes/add_node# rsync -av node01:/etc/kubernetes/bootstrap.kubeconfig .
   # 创建kube-proxy目录
   root@master:~/kubernetes/add_node# mkdir /root/kubernetes/add_node/kube-proxy/
   # 从现在有node01节点获取kube-proxy 证书文件
   root@master:~/kubernetes/add_node# rsync -av  node01:/etc/kubernetes/ca/kube-proxy/ /root/kubernetes/add_node/kube-proxy/
   # 从现在有node01节点获取kube-proxy.kubeconfig
   root@master:~/kubernetes/add_node# rsync -av  node01:/etc/kubernetes/kube-proxy.kubeconfig .
   # 复制config.properties到当前目录
   root@master:~/kubernetes/add_node# cp /root/kubernetes/kubernetes-starter/config.properties .
   # 创建add_node.py
   root@master:~/kubernetes/add_node# touch add_node.py
   # 授权可执行权限
   root@master:~/kubernetes/add_node# chmod +x add_node.py
   # 脚本内容
   root@master:~/kubernetes/add_node# cat add_node.py
   #!/usr/bin/env python3
   # -*- coding: utf-8 -*-
   import sys,time
   sys.path.append('/scripts/python/')
   from shell import Cmd,Remote_cmd
   class AddNode(object):
     def __init__(self,hostname):
         self.hostname = hostname
         self.local = Cmd()
         self.node = Remote_cmd('/root/.ssh/id_rsa',self.hostname,'22','root')
     def add_node(self):
         # Get kubernetes and extract
         print('[INFO] '+time.strftime("%Y-%m-%d %H:%M:%S")+' 安装git命令')
         self.node.realtime_shell('apt-get update && apt-get install -y git')
         print('[INFO] '+time.strftime("%Y-%m-%d %H:%M:%S")+' 获取kubernetes二进制文件及服务配置文件')
         self.node.realtime_shell('git clone https://code.aliyun.com/jy1779/kubernetes.git /root/kubernetes')
         print('[INFO] '+time.strftime("%Y-%m-%d %H:%M:%S")+' 解压kubernetes二进制文件压缩包')
         self.node.realtime_shell('tar xf ./kubernetes/kubernetes-bins.tar.gz -C /usr/local/sbin/ && rm -f ./kubernetes/kubernetes-bins.tar.gz && echo "export PATH=$PATH:/usr/local/sbin/kubernetes-bins" >> /etc/profile && source /etc/profile')
         # Install docker 
         print('[INFO] '+time.strftime("%Y-%m-%d %H:%M:%S")+' 安装docker及修改docker.service启动参数,关闭防火墙,设置内核配置转发')
         self.node.realtime_shell('curl -s  https://raw.githubusercontent.com/jy1779/docker/master/install/aliyun_docker_install.sh | bash')
   
         # Update 'ExecStartPost=/sbin/iptables -I FORWARD -s 0.0.0.0/0 -j ACCEPT' for  /lib/systemd/system/docker.service 
         # Restart docker
         line = self.node.onetime_shell('grep -n ExecStart /lib/systemd/system/docker.service|awk -F : \'{print $1}\'')
         execstartpost = 'ExecStartPost=/sbin/iptables -I FORWARD -s 0.0.0.0/0 -j ACCEPT'
         self.node.onetime_shell('sed "%s a%s" -i /lib/systemd/system/docker.service' %(line,execstartpost))
         self.node.onetime_shell('systemctl daemon-reload && service docker restart')
   
         # Disable ufw
         self.node.onetime_shell('ufw disable && ufw status')
         
         # config ip_forward
         self.node.onetime_shell('echo -e "net.ipv4.ip_forward = 1\\nnet.bridge.bridge-nf-call-ip6tables = 1\\nnet.bridge.bridge-nf-call-iptables = 1" >> /etc/sysctl.d/k8s.conf && sysctl -p /etc/sysctl.d/k8s.conf')
         
         # Update config.properties and sync node
         config_path = '/root/kubernetes/add_node/config.properties'
         node_config_path = '/root/kubernetes/kubernetes-starter/config.properties'
         node_ip = self.node.onetime_shell('ip address |grep ens|awk NR==2|awk -F  [" "/] \'{print $6}\'')
         self.local.onetime_shell('sed -i \'s/\(NODE_IP=\).*/\\1%s/\' %s' % (node_ip,config_path))
         self.local.realtime_shell('rsync -av %s %s:%s' % (config_path,self.hostname,node_config_path))
        
         # Get ca and bootstrap.kubeconfig for master
         self.node.onetime_shell('mkdir -p /etc/kubernetes/ca/')
         self.local.realtime_shell('rsync -av /etc/kubernetes/ca/ca*  %s:/etc/kubernetes/ca/'% self.hostname)
         self.local.realtime_shell('rsync -av /root/kubernetes/add_node/bootstrap.kubeconfig  %s:/etc/kubernetes/'% self.hostname )
         
         # Generate config file 
         self.node.realtime_shell('cd /root/kubernetes/kubernetes-starter/ && ./gen-config.sh with-ca')
         
         # Start calico service
         print('[INFO] '+time.strftime("%Y-%m-%d %H:%M:%S")+' 启动calico服务')
         self.node.realtime_shell('docker pull registry.cn-hangzhou.aliyuncs.com/jonny/pause-amd64:3.0')
         self.node.realtime_shell('cp ~/kubernetes/kubernetes-starter/target/all-node/kube-calico.service /lib/systemd/system/ && systemctl enable kube-calico.service && service kube-calico start')
       
         # Cni
         self.node.onetime_shell('mkdir -p /etc/cni/net.d/')
         self.node.onetime_shell('cp ~/kubernetes/kubernetes-starter/target/worker-node/10-calico.conf /etc/cni/net.d/')
         
         # Start kubelet
         print('[INFO] ' +time.strftime("%Y-%m-%d %H:%M:%S")+' 启动kubelet服务')
         self.node.onetime_shell('mkdir /var/lib/kubelet')
         self.node.realtime_shell('docker pull registry.cn-hangzhou.aliyuncs.com/imooc/pause-amd64:3.0')
         self.node.onetime_shell('cp ~/kubernetes/kubernetes-starter/target/worker-node/kubelet.service /lib/systemd/system/ && systemctl enable kubelet && service kubelet start')
   
   
         # Start kube-proxy
         print('[INFO] '+time.strftime("%Y-%m-%d %H:%M:%S")+' 启动kube-proxy服务')
         self.node.onetime_shell('mkdir -p /var/lib/kube-proxy /etc/kubernetes/ca/kube-proxy')
         self.local.realtime_shell('rsync -av /root/kubernetes/add_node/kube-proxy/* %s:/etc/kubernetes/ca/kube-proxy/' % self.hostname)
         self.local.realtime_shell('rsync -av /root/kubernetes/add_node/kube-proxy.kubeconfig %s:/etc/kubernetes/kube-proxy.kubeconfig' % self.hostname)
         self.node.realtime_shell('cp ~/kubernetes/kubernetes-starter/target/worker-node/kube-proxy.service /lib/systemd/system/ && systemctl enable kube-proxy.service && service kube-proxy start')
         # Master approve csr
         self.local.realtime_shell('sleep 5 && /usr/local/sbin/kubernetes-bins/kubectl get csr|grep \'Pending\' | awk \'{print $1}\'| xargs /usr/local/sbin/kubernetes-bins/kubectl certificate approve')
         print('[INFO] '+time.strftime("%Y-%m-%d %H:%M:%S")+' 安装完成')
   def help():
     print('输入node')
   if len(sys.argv) == 1:
      help()
   elif len(sys.argv) == 2:
      par = sys.argv[1:2]
      hostname = par[0]
      node = AddNode(hostname)
      node.add_node()
   else:
      help()
   # 执行添加节点脚本 
   # 输入hostname，必须做了免密才能执行脚本，以node02为例
   root@master:~/kubernetes/add_node# ./add_node.py node02
   [INFO] 2018-10-17 17:43:53 安装git命令
   Hit:1 http://mirrors.aliyun.com/docker-ce/linux/ubuntu xenial InRelease
   Hit:2 http://hk.archive.ubuntu.com/ubuntu xenial InRelease
   Hit:3 http://hk.archive.ubuntu.com/ubuntu xenial-updates InRelease
   Hit:4 http://hk.archive.ubuntu.com/ubuntu xenial-backports InRelease
   Get:5 http://security.ubuntu.com/ubuntu xenial-security InRelease [107 kB]
   Hit:6 http://ppa.launchpad.net/ansible/ansible/ubuntu xenial InRelease
   Fetched 107 kB in 8s (12.6 kB/s)
   Reading package lists...
   Reading package lists...
   Building dependency tree...
   Reading state information...
   git is already the newest version (1:2.7.4-0ubuntu1.5).
   0 upgraded, 0 newly installed, 0 to remove and 130 not upgraded.
   [INFO] 2018-10-17 17:44:20 获取kubernetes二进制文件及服务配置文件
   Cloning into '/root/kubernetes'...
   Checking out files: 100% (57/57), done.
   [INFO] 2018-10-17 17:46:08 解压kubernetes二进制文件压缩包
   [INFO] 2018-10-17 17:46:42 安装docker及修改docker.service启动参数,关闭防火墙,设置内核配置转发
   Hit:1 http://mirrors.aliyun.com/docker-ce/linux/ubuntu xenial InRelease
   Hit:2 http://hk.archive.ubuntu.com/ubuntu xenial InRelease
   Hit:3 http://hk.archive.ubuntu.com/ubuntu xenial-updates InRelease
   Hit:4 http://hk.archive.ubuntu.com/ubuntu xenial-backports InRelease
   Hit:5 http://security.ubuntu.com/ubuntu xenial-security InRelease
   Hit:6 http://ppa.launchpad.net/ansible/ansible/ubuntu xenial InRelease
   Reading package lists...
   Reading package lists...
   Building dependency tree...
   Reading state information...
   apt-transport-https is already the newest version (1.2.27).
   ca-certificates is already the newest version (20170717~16.04.1).
   curl is already the newest version (7.47.0-1ubuntu2.9).
   software-properties-common is already the newest version (0.96.20.7).
   0 upgraded, 0 newly installed, 0 to remove and 130 not upgraded.
   OK
   Hit:1 http://hk.archive.ubuntu.com/ubuntu xenial InRelease
   Hit:2 http://mirrors.aliyun.com/docker-ce/linux/ubuntu xenial InRelease
   Hit:3 http://hk.archive.ubuntu.com/ubuntu xenial-updates InRelease
   Hit:4 http://hk.archive.ubuntu.com/ubuntu xenial-backports InRelease
   Hit:5 http://security.ubuntu.com/ubuntu xenial-security InRelease
   Hit:6 http://ppa.launchpad.net/ansible/ansible/ubuntu xenial InRelease
   Reading package lists...
   Reading package lists...
   Building dependency tree...
   Reading state information...
   docker-ce is already the newest version (18.06.1~ce~3-0~ubuntu).
   0 upgraded, 0 newly installed, 0 to remove and 130 not upgraded.
   Docker version 18.06.1-ce, build e68fc7a
   sending incremental file list
   config.properties
   
   sent 622 bytes  received 41 bytes  442.00 bytes/sec
   total size is 519  speedup is 0.78
   sending incremental file list
   ca-config.json
   ca-csr.json
   ca-key.pem
   ca.csr
   ca.pem
   calico/
   calico/calico-csr.json
   calico/calico-key.pem
   calico/calico.csr
   calico/calico.pem
   
   sent 9,430 bytes  received 199 bytes  6,419.33 bytes/sec
   total size is 8,770  speedup is 0.91
   sending incremental file list
   bootstrap.kubeconfig
   
   sent 2,278 bytes  received 35 bytes  4,626.00 bytes/sec
   total size is 2,172  speedup is 0.94
   ====替换变量列表====
   BIN_PATH=/usr/local/sbin/kubernetes-bins
   NODE_IP=192.168.1.74
   ETCD_ENDPOINTS=https://192.168.1.72:2379,https://192.168.1.73:2379,https://192.168.1.74:2379
   MASTER_IP=192.168.1.72
   ====================
   ====替换配置文件====
   all-node/kube-calico.service
   ca/admin/admin-csr.json
   ca/ca-config.json
   ca/ca-csr.json
   ca/calico/calico-csr.json
   ca/etcd/etcd-csr.json
   ca/kube-proxy/kube-proxy-csr.json
   ca/kubernetes/kubernetes-csr.json
   master-node/etcd.service
   master-node/kube-apiserver.service
   master-node/kube-controller-manager.service
   master-node/kube-scheduler.service
   services/kube-dashboard.yaml
   services/kube-dns.yaml
   worker-node/10-calico.conf
   worker-node/kubelet.service
   worker-node/kube-proxy.service
   =================
   配置生成成功，位置: /root/kubernetes/kubernetes-starter/target
   [INFO] 2018-10-17 17:47:28 启动calico服务
   v2.6.2: Pulling from jonny/calico-node
   6d987f6f4279: Pulling fs layer
   451e44d240b0: Pulling fs layer
   564d30bd7dc2: Pulling fs layer
   39b8f29b8ec9: Pulling fs layer
   cd8e6a6bdbfe: Pulling fs layer
   39b8f29b8ec9: Waiting
   cd8e6a6bdbfe: Waiting
   564d30bd7dc2: Verifying Checksum
   564d30bd7dc2: Download complete
   6d987f6f4279: Verifying Checksum
   6d987f6f4279: Download complete
   6d987f6f4279: Pull complete
   451e44d240b0: Verifying Checksum
   451e44d240b0: Download complete
   39b8f29b8ec9: Verifying Checksum
   39b8f29b8ec9: Download complete
   451e44d240b0: Pull complete
   564d30bd7dc2: Pull complete
   39b8f29b8ec9: Pull complete
   cd8e6a6bdbfe: Verifying Checksum
   cd8e6a6bdbfe: Download complete
   cd8e6a6bdbfe: Pull complete
   Digest: sha256:2d5255fab62c29226a9a4121e1251439c2861641532edd653a009c11f4ec1b4f
   Status: Downloaded newer image for registry.cn-hangzhou.aliyuncs.com/jonny/calico-node:v2.6.2
   Created symlink from /etc/systemd/system/multi-user.target.wants/kube-calico.service to /lib/systemd/system/kube-calico.service.
   [INFO] 2018-10-17 17:48:09 启动kubelet服务
   3.0: Pulling from imooc/pause-amd64
   4f4fb700ef54: Pulling fs layer
   ce150f7a21ec: Pulling fs layer
   4f4fb700ef54: Verifying Checksum
   4f4fb700ef54: Download complete
   4f4fb700ef54: Pull complete
   ce150f7a21ec: Verifying Checksum
   ce150f7a21ec: Download complete
   ce150f7a21ec: Pull complete
   Digest: sha256:f04288efc7e65a84be74d4fc63e235ac3c6c603cf832e442e0bd3f240b10a91b
   Status: Downloaded newer image for registry.cn-hangzhou.aliyuncs.com/jonny/pause-amd64:3.0
   [INFO] 2018-10-17 17:48:14 启动kube-proxy服务
   sending incremental file list
   kube-proxy-csr.json
   kube-proxy-key.pem
   kube-proxy.csr
   kube-proxy.pem
   
   sent 4,588 bytes  received 92 bytes  1,040.00 bytes/sec
   total size is 4,292  speedup is 0.92
   sending incremental file list
   kube-proxy.kubeconfig
   
   sent 6,361 bytes  received 35 bytes  4,264.00 bytes/sec
   total size is 6,254  speedup is 0.98
   Created symlink from /etc/systemd/system/multi-user.target.wants/kube-proxy.service to /lib/systemd/system/kube-proxy.service.
   certificatesigningrequest "node-csr-eBzTrAajZuhbRg8HKofPZ5DtRlH2g3m2aehQaIjz_wo" approved
   [INFO] 2018-10-17 17:48:43 安装完成
   
   root@master:~/kubernetes/add_node# kubectl get node
   NAME           STATUS    ROLES     AGE       VERSION
   192.168.1.73   Ready     <none>    6h        v1.9.0
   192.168.1.74   Ready     <none>    2m        v1.9.0 #新增节点node02，状态为Ready，正常
   
   #最后的etcd-2节点不再演示部署，已经测试过没问题。
   ```

## 1.7 部署监控(influxdb+heapster+grafana)

```shell
root@master:~/kubernetes/monitor# cat influxdb.yaml 
apiVersion: extensions/v1beta1
kind: Deployment
metadata:
  name: monitoring-influxdb
  namespace: kube-system
spec:
  replicas: 1
  template:
    metadata:
      labels:
        task: monitoring
        k8s-app: influxdb
    spec:
      containers:
      - name: influxdb
        image: registry.cn-hangzhou.aliyuncs.com/jonny/heapster-influxdb-amd64:v1.3.3
        volumeMounts:
        - mountPath: /data
          name: influxdb-storage
      volumes:
      - name: influxdb-storage
        emptyDir: {}

---

apiVersion: v1
kind: Service
metadata:
  labels:
    task: monitoring
    # For use as a Cluster add-on (https://github.com/kubernetes/kubernetes/tree/master/cluster/addons)
    # If you are NOT using this as an addon, you should comment out this line.
    kubernetes.io/cluster-service: 'true'
    kubernetes.io/name: monitoring-influxdb
  name: monitoring-influxdb
  namespace: kube-system
spec:
  ports:
  - port: 8086
    targetPort: 8086
  selector:
    k8s-app: influxdb
root@master:~/kubernetes/monitor# cat heapster.yaml 
apiVersion: v1
kind: ServiceAccount
metadata:
  name: heapster
  namespace: kube-system
---
apiVersion: rbac.authorization.k8s.io/v1beta1
kind: ClusterRoleBinding
metadata:
  name: heapster
roleRef:
  kind: ClusterRole
  name: cluster-admin
  apiGroup: rbac.authorization.k8s.io
subjects:
  - kind: ServiceAccount
    name: heapster
    namespace: kube-system

---

apiVersion: extensions/v1beta1
kind: Deployment
metadata:
  name: heapster
  namespace: kube-system
spec:
  replicas: 1
  template:
    metadata:
      labels:
        task: monitoring
        k8s-app: heapster
    spec:
      serviceAccountName: heapster
      containers:
      - name: heapster
        image: registry.cn-hangzhou.aliyuncs.com/jonny/heapster-amd64:v1.4.2
        imagePullPolicy: IfNotPresent
        command:
        - /heapster
        - --source=kubernetes:https://kubernetes.default
        - --sink=influxdb:http://monitoring-influxdb:8086

---

apiVersion: v1
kind: Service
metadata:
  labels:
    task: monitoring
    # For use as a Cluster add-on (https://github.com/kubernetes/kubernetes/tree/master/cluster/addons)
    # If you are NOT using this as an addon, you should comment out this line.
    kubernetes.io/cluster-service: 'true'
    kubernetes.io/name: Heapster
  name: heapster
  namespace: kube-system
spec:
  ports:
  - port: 80
    targetPort: 8082
  selector:
    k8s-app: heapster
root@master:~/kubernetes/monitor# cat grafana.yaml 
apiVersion: extensions/v1beta1
kind: Deployment
metadata:
  name: monitoring-grafana
  namespace: kube-system
spec:
  replicas: 1
  template:
    metadata:
      labels:
        task: monitoring
        k8s-app: grafana
    spec:
      containers:
      - name: grafana
        image: registry.cn-hangzhou.aliyuncs.com/jonny/heapster-grafana-amd64:v4.4.3
        ports:
          - containerPort: 3000
            protocol: TCP
        volumeMounts:
        - mountPath: /var
          name: grafana-storage
        env:
        - name: INFLUXDB_HOST
          value: monitoring-influxdb
        - name: GRAFANA_PORT
          value: "3000"
          # The following env variables are required to make Grafana accessible via
          # the kubernetes api-server proxy. On production clusters, we recommend
          # removing these env variables, setup auth for grafana, and expose the grafana
          # service using a LoadBalancer or a public IP.
        - name: GF_AUTH_BASIC_ENABLED
          value: "false"
        - name: GF_AUTH_ANONYMOUS_ENABLED
          value: "true"
        - name: GF_AUTH_ANONYMOUS_ORG_ROLE
          value: Admin
        - name: GF_SERVER_ROOT_URL
          # If you're only using the API Server proxy, set this value instead:
          value: /
      volumes:
      - name: grafana-storage
        emptyDir: {}

---

apiVersion: v1
kind: Service
metadata:
  labels:
    # For use as a Cluster add-on (https://github.com/kubernetes/kubernetes/tree/master/cluster/addons)
    # If you are NOT using this as an addon, you should comment out this line.
    kubernetes.io/cluster-service: 'true'
    kubernetes.io/name: monitoring-grafana
  name: monitoring-grafana
  namespace: kube-system
spec:
  # In a production setup, we recommend accessing Grafana through an external Loadbalancer
  # or through a public IP.
  # type: LoadBalancer
  type: NodePort
  ports:
  - port : 80
    targetPort: 3000
  selector:
    k8s-app: grafana
root@master:~/kubernetes/monitor# kubectl apply -f influxdb.yaml
root@master:~/kubernetes/monitor# kubectl apply -f heapster.yaml
root@master:~/kubernetes/monitor# kubectl apply -f grafana.yaml
root@master:~/kubernetes/monitor# kubectl -n kube-system get pods|grep  -E 'influxdb|grafana|heapster'
heapster-7db7b86576-v48q6              1/1       Running   0          3m
monitoring-grafana-6854bc4b4d-tz7gk    1/1       Running   0          3m
monitoring-influxdb-789c759c45-6lqlb   1/1       Running   0          3m

# 查看grafana，使用节点IP+26007访问，例如:http://192.168.1.73:26007
root@master:~/kubernetes/monitor# kubectl -n kube-system get service|grep grafana
monitoring-grafana     NodePort    10.68.182.115   <none>        80:26007/TCP    6m
```

访问URL：http://192.168.1.73:26007

![](https://raw.githubusercontent.com/jy1779/doc/master/image/kubernetes/grafana.png)


