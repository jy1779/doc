# 部署k8s集群

1.1安装docker

```shell
curl -s  https://raw.githubusercontent.com/jy1779/docker/master/install/aliyun_docker_install.sh | bash
```

修改docker.server

```shell
LINE=$(grep -n ExecStart /lib/systemd/system/docker.service|awk -F : '{print $1}')
EXECSTARTPOST='ExecStartPost=/sbin/iptables -I FORWARD -s 0.0.0.0/0 -j ACCEPT'
sed "$LINE a$EXECSTARTPOST" -i /lib/systemd/system/docker.service
#重启docker
systemctl daemon-reload && service docker restart
```

关闭防火墙

```shell
ufw disable && ufw status
```

写入配置文件

```shell
cat <<EOF > /etc/sysctl.d/k8s.conf
net.ipv4.ip_forward = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
EOF
```

生效配置文件

```shell
sysctl -p /etc/sysctl.d/k8s.conf
```

添加hosts文件

```shell
echo -e "192.168.1.72 master\n192.168.1.73 node01" >> /etc/hosts
```



2、获取kubenetes

```shell
git clone https://code.aliyun.com/jy1779/kubernetes.git
#解压kubernetes-bins,添加到环境变量
tar xf ./kubernetes/kubernetes-bins.tar.gz -C /usr/local/sbin/ && rm -f ./kubernetes/kubernetes-bins.tar.gz
echo 'export PATH=$PATH:/usr/local/sbin/kubernetes-bins' >> /etc/profile && source /etc/profile
```

3、生成配置文件

```shell
cd /root/kubernetes/kubernetes-starter/
修改配置文件
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
```

4、安装cfssl

```shell
wget -q --show-progress --https-only --timestamping \
  https://pkg.cfssl.org/R1.2/cfssl_linux-amd64 \
  https://pkg.cfssl.org/R1.2/cfssljson_linux-amd64
 #修改为可执行权限
chmod +x cfssl_linux-amd64 cfssljson_linux-amd64
#移动到bin目录
mv cfssl_linux-amd64 /usr/local/bin/cfssl
mv cfssljson_linux-amd64 /usr/local/bin/cfssljson
#验证
cfssl version
```



5、生成根证书（主节点）

```shell
#所有证书相关的东西都放在这
mkdir -p /etc/kubernetes/ca
#准备生成证书的配置文件
cp ~/kubernetes/kubernetes-starter/target/ca/ca-config.json /etc/kubernetes/ca
cp ~/kubernetes/kubernetes-starter/target/ca/ca-csr.json /etc/kubernetes/ca
#生成证书和秘钥
cd /etc/kubernetes/ca

cfssl gencert -initca ca-csr.json | cfssljson -bare ca

```





6、部署etcd  
6.1 准备证书
etcd节点需要提供给其他服务访问，就要验证其他服务的身份，所以需要一个标识自己监听服务的server证书，当有多个etcd节点的时候也需要client证书与etcd集群其他节点交互，当然也可以client和server使用同一个证书因为它们本质上没有区别。

```shell
#etcd证书放在这
mkdir -p /etc/kubernetes/ca/etcd
#准备etcd证书配置
cp ~/kubernetes/kubernetes-starter/target/ca/etcd/etcd-csr.json /etc/kubernetes/ca/etcd/
cd /etc/kubernetes/ca/etcd/
#使用根证书(ca.pem)签发etcd证书
cfssl gencert \
        -ca=/etc/kubernetes/ca/ca.pem \
        -ca-key=/etc/kubernetes/ca/ca-key.pem \
        -config=/etc/kubernetes/ca/ca-config.json \
        -profile=kubernetes etcd-csr.json | cfssljson -bare etcd
#跟之前类似生成三个文件etcd.csr是个中间证书请求文件，我们最终要的是etcd-key.pem和etcd.pem
ls
etcd.csr  etcd-csr.json  etcd-key.pem  etcd.pem

6.2 启动etcd服务
#创建工作目录(保存数据的地方)
mkdir -p /var/lib/etcd
#把服务配置文件copy到系统服务目录
cp ~/kubernetes/kubernetes-starter/target/master-node/etcd.service /lib/systemd/system/

systemctl enable etcd.service
#启动服务
service etcd start

查看服务日志，看是否有错误信息，确保服务正常

journalctl -f -u etcd.service

#测试etcd
ETCDCTL_API=3 etcdctl \
  --endpoints=https://192.168.1.72:2379  \
  --cacert=/etc/kubernetes/ca/ca.pem \
  --cert=/etc/kubernetes/ca/etcd/etcd.pem \
  --key=/etc/kubernetes/ca/etcd/etcd-key.pem \
  endpoint health

#显示以下则为部署成功。

https://192.168.1.72:2379 is healthy: successfully committed proposal: took = 10.408412ms

```

7、部署APIServer（主节点）
#准备证书
#api-server证书放在这，api-server是核心，文件夹叫kubernetes吧，如果想叫apiserver也可以，不过相关的地方都需要修改哦

```shell
mkdir -p /etc/kubernetes/ca/kubernetes
#准备apiserver证书配置
cp ~/kubernetes/kubernetes-starter/target/ca/kubernetes/kubernetes-csr.json /etc/kubernetes/ca/kubernetes/
#使用根证书(ca.pem)签发kubernetes证书
cd /etc/kubernetes/ca/kubernetes/
cfssl gencert \
        -ca=/etc/kubernetes/ca/ca.pem \
        -ca-key=/etc/kubernetes/ca/ca-key.pem \
        -config=/etc/kubernetes/ca/ca-config.json \
        -profile=kubernetes kubernetes-csr.json | cfssljson -bare kubernetes
#跟之前类似生成三个文件kubernetes.csr是个中间证书请求文件，我们最终要的是kubernetes-key.pem和kubernetes.pem
ls
kubernetes.csr  kubernetes-csr.json  kubernetes-key.pem  kubernetes.pem

#生成token认证文件
#生成随机token
head -c 16 /dev/urandom | od -An -t x | tr -d ' '

root@master:/etc/kubernetes/ca/kubernetes# head -c 16 /dev/urandom | od -An -t x | tr -d ' '
97e8c07dce2b2bab69cfd3162d5383c9

echo "97e8c07dce2b2bab69cfd3162d5383c9,kubelet-bootstrap,10001,"system:kubelet-bootstrap"" > /etc/kubernetes/ca/kubernetes/token.csv

#启动api-server服务
cp ~/kubernetes/kubernetes-starter/target/master-node/kube-apiserver.service /lib/systemd/system/
systemctl enable kube-apiserver.service
service kube-apiserver start
journalctl -f -u kube-apiserver

```

8、部署controller-manager
controller-manager一般与api-server在同一台机器上，所以可以使用非安全端口与api-server通讯，不需要生成证书和私钥。

```shell
cp ~/kubernetes/kubernetes-starter/target/master-node/kube-controller-manager.service /lib/systemd/system/
systemctl enable kube-controller-manager.service
service kube-controller-manager start
journalctl -f -u kube-controller-manager

#启动scheduler服务
cp ~/kubernetes/kubernetes-starter/target/master-node/kube-scheduler.service /lib/systemd/system/
systemctl enable kube-scheduler.service
service kube-scheduler start
journalctl -f -u kube-scheduler
```



9、配置kubectl
9.1准备证书
#kubectl证书放在这，由于kubectl相当于系统管理员，我们使用admin命名

```shell
mkdir -p /etc/kubernetes/ca/admin
#准备admin证书配置 - kubectl只需客户端证书，因此证书请求中 hosts 字段可以为空
cp ~/kubernetes/kubernetes-starter/target/ca/admin/admin-csr.json /etc/kubernetes/ca/admin/
#使用根证书(ca.pem)签发admin证书
cd /etc/kubernetes/ca/admin/
cfssl gencert \
        -ca=/etc/kubernetes/ca/ca.pem \
        -ca-key=/etc/kubernetes/ca/ca-key.pem \
        -config=/etc/kubernetes/ca/ca-config.json \
        -profile=kubernetes admin-csr.json | cfssljson -bare admin
#我们最终要的是admin-key.pem和admin.pem
ls
admin.csr  admin-csr.json  admin-key.pem  admin.pem

配置kubectl文件
#指定apiserver的地址和证书位置
kubectl config set-cluster kubernetes \
        --certificate-authority=/etc/kubernetes/ca/ca.pem \
        --embed-certs=true \
        --server=https://192.168.1.72:6443
#设置客户端认证参数，指定admin证书和秘钥
kubectl config set-credentials admin \
        --client-certificate=/etc/kubernetes/ca/admin/admin.pem \
        --embed-certs=true \
        --client-key=/etc/kubernetes/ca/admin/admin-key.pem
#关联用户和集群
kubectl config set-context kubernetes \
        --cluster=kubernetes --user=admin
#设置当前上下文
kubectl config use-context kubernetes
#设置结果就是一个配置文件，可以看看内容

cat ~/.kube/config

验证master节点
kubectl get componentstatus

```



10.部署CalicoNode
Calico实现了CNI接口，是kubernetes网络方案的一种选择，它一个纯三层的数据中心网络方案（不需要Overlay），并且与OpenStack、Kubernetes、AWS、GCE等IaaS和容器平台都有良好的集成。 Calico在每一个计算节点利用Linux Kernel实现了一个高效的vRouter来负责数据转发，而每个vRouter通过BGP协议负责把自己上运行的workload的路由信息像整个Calico网络内传播——小规模部署可以直接互联，大规模下可通过指定的BGP route reflector来完成。 这样保证最终所有的workload之间的数据流量都是通过IP路由的方式完成互联的。

 #准备证书

后续可以看到calico证书用在四个地方：

```shell
calico/node 这个docker 容器运行时访问 etcd 使用证书
cni 配置文件中，cni 插件需要访问 etcd 使用证书
calicoctl 操作集群网络时访问 etcd 使用证书
calico/kube-controllers 同步集群网络策略时访问 etcd 使用证书
#calico证书放在这
mkdir -p /etc/kubernetes/ca/calico
#准备calico证书配置 - calico只需客户端证书，因此证书请求中 hosts 字段可以为空
cp ~/kubernetes/kubernetes-starter/target/ca/calico/calico-csr.json /etc/kubernetes/ca/calico/
cd /etc/kubernetes/ca/calico/
cfssl gencert \
        -ca=/etc/kubernetes/ca/ca.pem \
        -ca-key=/etc/kubernetes/ca/ca-key.pem \
        -config=/etc/kubernetes/ca/ca-config.json \
        -profile=kubernetes calico-csr.json | cfssljson -bare calico
#我们最终要的是calico-key.pem和calico.pem
ls 
calico.csr  calico-csr.json  calico-key.pem  calico.pem
#启动服务
cp ~/kubernetes/kubernetes-starter/target/all-node/kube-calico.service /lib/systemd/system/
systemctl enable kube-calico.service
service kube-calico start
journalctl -f -u kube-calico
#查看节点情况
calicoctl node status
```


11.部署kuberneter节点

1.安装docker

```shell
curl -s  https://raw.githubusercontent.com/jy1779/docker/master/install/aliyun_docker_install.sh | bash
```

2.获取kuberneter二进制文件

```shell
git clone https://code.aliyun.com/jy1779/kubernetes.git	
#解压kubernetes-bins,添加到环境变量
tar xf ./kubernetes/kubernetes-bins.tar.gz -C /usr/local/sbin/
echo 'export PATH=$PATH:/usr/local/sbin/kubernetes-bins' >> /etc/profile && source /etc/profile
#修改docker.server
LINE=$(grep -n ExecStart /lib/systemd/system/docker.service|awk -F : '{print $1}')
EXECSTARTPOST='ExecStartPost=/sbin/iptables -I FORWARD -s 0.0.0.0/0 -j ACCEPT'
sed "$LINE a$EXECSTARTPOST" -i /lib/systemd/system/docker.service
#重启docker
systemctl daemon-reload && service docker restart

#关闭防火墙
ufw disable && ufw status
#写入配置文件
cat <<EOF > /etc/sysctl.d/k8s.conf
net.ipv4.ip_forward = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
EOF
#生效配置文件
sysctl -p /etc/sysctl.d/k8s.conf

#修改配置文件config.properties

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

cd ~/kubernetes/kubernetes-starter && ./gen-config.sh with-ca

#安装cfssl
wget -q --show-progress --https-only --timestamping \
  https://pkg.cfssl.org/R1.2/cfssl_linux-amd64 \
  https://pkg.cfssl.org/R1.2/cfssljson_linux-amd64
chmod +x cfssl_linux-amd64 cfssljson_linux-amd64
mv cfssl_linux-amd64 /usr/local/bin/cfssl
mv cfssljson_linux-amd64 /usr/local/bin/cfssljson
cfssl version

#创建目录
mkdir -p /etc/kubernetes/ca/

#从master获取calico证书

rsync -av 192.168.1.72:/etc/kubernetes/ca/ca* /etc/kubernetes/ca/

#启动calico服务

cp ~/kubernetes/kubernetes-starter/target/all-node/kube-calico.service /lib/systemd/system/

systemctl enable kube-calico.service
service kube-calico start

查看calico节点

calicoctl node status

创建bootstrap.kubeconfig

cd /etc/kubernetes/

#创建bootstrap.kubeconfig
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

准备cni

mkdir -p /etc/cni/net.d/

cp ~/kubernetes/kubernetes-starter/target/worker-node/10-calico.conf /etc/cni/net.d/

部署kubelet服务

在master执行创建该用户

kubectl create clusterrolebinding kubelet-bootstrap --clusterrole=system:node-bootstrapper --user=kubelet-bootstrap

mkdir /var/lib/kubelet

cp ~/kubernetes/kubernetes-starter/target/worker-node/kubelet.service /lib/systemd/system/
systemctl enable kubelet
systemctl daemon-reload
service kubelet start

在master执行

查看csr

kubectl get csr
NAME                                                   AGE       REQUESTOR           CONDITION
node-csr-xNqwjv6k56NdkqbEpoinSOKEekPXrMvI6EgUGzTrngk   1m        kubelet-bootstrap   Pending
允许请求

kubectl get csr|grep 'Pending' | awk '{print $1}'| xargs kubectl certificate approve
certificatesigningrequest "node-csr-xNqwjv6k56NdkqbEpoinSOKEekPXrMvI6EgUGzTrngk" approved
再次查看 kubectl get csr
NAME                                                   AGE       REQUESTOR           CONDITION
node-csr-xNqwjv6k56NdkqbEpoinSOKEekPXrMvI6EgUGzTrngk   1m        kubelet-bootstrap   Approved,Issued

部署kube-proxy

mkdir -p /var/lib/kube-proxy
mkdir -p /etc/kubernetes/ca/kube-proxy
#复制kube-proxy服务配置文件
cp ~/kubernetes/kubernetes-starter/target/ca/kube-proxy/kube-proxy-csr.json /etc/kubernetes/ca/kube-proxy/

cd /etc/kubernetes/ca/kube-proxy/
#使用根证书(ca.pem)签发calico证书

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

cp ~/kubernetes/kubernetes-starter/target/worker-node/kube-proxy.service /lib/systemd/system/
systemctl daemon-reload
apt install conntrack #没有安装
service kube-proxy start

```



验证kube-proxy

```shell
root@master:~# kubectl get pods
NAME                     READY     STATUS    RESTARTS   AGE
nginx-65dbdf6899-s66w6   1/1       Running   0          37m
root@master:~# kubectl get service
NAME            TYPE        CLUSTER-IP    EXTERNAL-IP   PORT(S)   AGE
kubernetes      ClusterIP   10.68.0.1     <none>        443/TCP   1h
nginx-service   ClusterIP   10.68.81.75   <none>        80/TCP    35m
root@master:~# kubectl exec -it nginx-65dbdf6899-s66w6 bash
bash-4.3# curl -I  10.68.81.75
HTTP/1.1 200 OK
Server: nginx/1.9.14
Date: Wed, 26 Sep 2018 09:40:18 GMT
Content-Type: text/html
Content-Length: 612
Last-Modified: Wed, 21 Sep 2016 08:11:20 GMT
Connection: keep-alive
ETag: "57e240a8-264"
Accept-Ranges: bytes
```

在节点上验证

```shell
root@node01:/etc/kubernetes/ca/kube-proxy# curl -I  10.68.81.75
HTTP/1.1 200 OK
Server: nginx/1.9.14
Date: Wed, 26 Sep 2018 09:40:24 GMT
Content-Type: text/html
Content-Length: 612
Last-Modified: Wed, 21 Sep 2016 08:11:20 GMT
Connection: keep-alive
ETag: "57e240a8-264"
Accept-Ranges: bytes

```

部署dns

kube-dns.yaml

```yaml
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

```

验证dns

```shell
root@master:~# kubectl get pods
NAME                     READY     STATUS    RESTARTS   AGE
nginx-65dbdf6899-s66w6   1/1       Running   0          34m
root@master:~# kubectl get service
NAME            TYPE        CLUSTER-IP    EXTERNAL-IP   PORT(S)   AGE
kubernetes      ClusterIP   10.68.0.1     <none>        443/TCP   1h
nginx-service   ClusterIP   10.68.81.75   <none>        80/TCP    32m
root@master:~# kubectl exec -it nginx-65dbdf6899-s66w6 bash
bash-4.3# curl -I nginx-service
HTTP/1.1 200 OK
Server: nginx/1.9.14
Date: Wed, 26 Sep 2018 09:37:27 GMT
Content-Type: text/html
Content-Length: 612
Last-Modified: Wed, 21 Sep 2016 08:11:20 GMT
Connection: keep-alive
ETag: "57e240a8-264"
Accept-Ranges: bytes

```

部署dashboard

kube-dashboard.yaml 

访问验证

https://192.168.1.73:9443/#!/login

创建token

admin-role.yaml 

```yaml
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

```

```shell
kubectl apply -f admin-role.yaml
kubectl -n kube-system get secret admin-token-fjjgt
NAME                TYPE                                  DATA      AGE
admin-token-fjjgt   kubernetes.io/service-account-token   3         8m
#查看token,使用该token登录
 kubectl -n kube-system  get secret admin-token-fjjgt -o jsonpath={.data.token}| base64 -d
 eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJrdWJlLXN5c3RlbSIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VjcmV0Lm5hbWUiOiJhZG1pbi10b2tlbi1zZHB4eiIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50Lm5hbWUiOiJhZG1pbiIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50LnVpZCI6IjBiNzkzODlhLWNjMzAtMTFlOC1hYjE4LTAwMGMyOTYzYWFjYyIsInN1YiI6InN5c3RlbTpzZXJ2aWNlYWNjb3VudDprdWJlLXN5c3RlbTphZG1pbiJ9.g-J9hV2dP2O679QvSfX5ANnO3cwVcYU31UVj_WQXmg52dPCLtX9Y5UcFh9oZaw6r6zrgFvJuk3JEMfvCGEQSgfxp2JWMaS307mFXnqBbBK4VwWWHHbGg4b_BHO7O18uBpLplKjYPZtnkeWBj7Bgj-DuNcOrpBvZWXJrXFf4xLMfJYomMhpRIWIkGX_Vef504bw4NoGaJLMPGd9aUyjTkMr78vOdK-C9Vq_h5Aaf01PSlA_JJ0adLzZgFGrj_mGeA6m8PdQ93b2BAf7PY9vkvrgB_1YaursNmZ0XhxVRhSDZ3V6SuUjoTN8SmcTVd5BkcVVY_AbwHFSxxHcHRQ0M_WQ
 
```



