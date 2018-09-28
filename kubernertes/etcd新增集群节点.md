k8s etcd新增集群节点

etcd执行添加节点

```shell
root@master:~/kubernetes/service# ETCDCTL_API=3 etcdctl   --endpoints=https://192.168.1.72:2379   --cacert=/etc/kubernetes/ca/ca.pem   --cert=/etc/kubernetes/ca/etcd/etcd.pem   --key=/etc/kubernetes/ca/etcd/etcd-key.pem   member add 192.168.1.74 --peer-urls=https://192.168.1.74:2380
Member 649537debe87e4cf added to cluster  5867db71109a61d
#以下三个变量需要添加到etcd节点启动服务文件
ETCD_NAME="192.168.1.74"
ETCD_INITIAL_CLUSTER="192.168.1.72=https://192.168.1.72:2380,192.168.1.74=https://192.168.1.74:2380,192.168.1.73=https://192.168.1.73:2380"
ETCD_INITIAL_CLUSTER_STATE="existing"
```

启动etcd节点

```shell
#创建保存etc证书的目录
mkdir /etc/kubernetes/ca/etcd
#将生成etcd的json文件拷贝到/etc/kubernetes/ca/etcd
cp ~/kubernetes/kubernetes-starter/target/ca/etcd/etcd-csr.json /etc/kubernetes/ca/etcd/
#切换到该目录
cd /etc/kubernetes/ca/etcd
#生成etcd证书
cfssl gencert \
        -ca=/etc/kubernetes/ca/ca.pem \
        -ca-key=/etc/kubernetes/ca/ca-key.pem \
        -config=/etc/kubernetes/ca/ca-config.json \
        -profile=kubernetes etcd-csr.json | cfssljson -bare etcd
#查看目录
root@node02:/etc/kubernetes/ca/etcd# ls
etcd.csr  etcd-csr.json  etcd-key.pem  etcd.pem
#创建etcd数据目录
mkdir -p /var/lib/etcd
#复制etcd服务启动文件
cp -a  kubernetes/kubernetes-starter/target/master-node/etcd.service /lib/systemd/system/
#添加以下三个参数
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
  --name=192.168.1.74 \
  --listen-client-urls=https://192.168.1.74:2379,http://127.0.0.1:2379 \
  --advertise-client-urls=https://192.168.1.74:2379 \
  --data-dir=/var/lib/etcd \
  --listen-peer-urls=https://192.168.1.74:2380 \
  --initial-advertise-peer-urls=https://192.168.1.74:2380 \
--initial-cluster="192.168.1.72=https://192.168.1.72:2380,192.168.1.74=https://192.168.1.74:2380,192.168.1.73=https://192.168.1.73:2380"
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
#创建etcd服务
systemctl enable etcd.service 
#启动etcd服务
service etcd start
#检查etcd节点
ETCDCTL_API=3 etcdctl   --endpoints=https://192.168.1.74:2379   --cacert=/etc/kubernetes/ca/ca.pem   --cert=/etc/kubernetes/ca/etcd/etcd.pem   --key=/etc/kubernetes/ca/etcd/etcd-key.pem   member list
5c81b5ea448e2eb, started, 192.168.1.72, https://192.168.1.72:2380, https://192.168.1.72:2379
649537debe87e4cf, started, 192.168.1.74, https://192.168.1.74:2380, https://192.168.1.74:2379
c39c45ea12ff2451, started, 192.168.1.73, https://192.168.1.73:2380, https://192.168.1.73:2379
```







