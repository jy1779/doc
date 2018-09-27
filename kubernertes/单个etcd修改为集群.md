单个etcd修改为集群

etcd启动配置文件

```shell
root@master:~/kubernetes/service# cat /lib/systemd/system/etcd.service 
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
  --initial-cluster=192.168.1.72=https://192.168.1.72:2380 \  #添加集群
  --initial-cluster-token=etcd-cluster \  #集群token
  --initial-cluster-state=new \  #第一次集群状态为new
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

```



查看etcd集群节点成员，目前只有自己

```shell
root@master:~/kubernetes/service# ETCDCTL_API=3 etcdctl   --endpoints=https://192.168.1.72:2379   --cacert=/etc/kubernetes/ca/ca.pem   --cert=/etc/kubernetes/ca/etcd/etcd.pem   --key=/etc/kubernetes/ca/etcd/etcd-key.pem   member list
5c81b5ea448e2eb, started, 192.168.1.72, https://192.168.1.72:2380, https://192.168.1.72:2379
```

添加etcd集群成员

```shell
root@master:~# ETCDCTL_API=3 etcdctl   --endpoints=https://192.168.1.72:2379   --cacert=/etc/kubernetes/ca/ca.pem   --cert=/etc/kubernetes/ca/etcd/etcd.pem   --key=/etc/kubernetes/ca/etcd/etcd-key.pem   member add 192.168.1.73 --peer-urls=https://192.168.1.73:2380
Member c39c45ea12ff2451 added to cluster  5867db71109a61d
#出现以下三个变量，将该变量写入etcd成员的启动配置文件
ETCD_NAME="192.168.1.73"
ETCD_INITIAL_CLUSTER="192.168.1.72=https://192.168.1.72:2380,192.168.1.73=https://192.168.1.73:2380"
ETCD_INITIAL_CLUSTER_STATE="existing"
```

etcd集群成员启动，新增以下参数：

--name=192.168.1.73

--initial-cluster=192.168.1.72=https://192.168.1.72:2380,192.168.1.73=https://192.168.1.73:2380

--initial-cluster-state=existing

```shell
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

```

健康检查

ETCDCTL_API=3 etcdctl \
  --endpoints=https://192.168.1.72:2379,https://192.168.1.73:2379 \
  --cacert=/etc/kubernetes/ca/ca.pem \
  --cert=/etc/kubernetes/ca/etcd/etcd.pem \
  --key=/etc/kubernetes/ca/etcd/etcd-key.pem \
  endpoint health

```shell
root@master:~/kubernetes/service# ETCDCTL_API=3 etcdctl \
>   --endpoints=https://192.168.1.72:2379,https://192.168.1.73:2379 \
>   --cacert=/etc/kubernetes/ca/ca.pem \
>   --cert=/etc/kubernetes/ca/etcd/etcd.pem \
>   --key=/etc/kubernetes/ca/etcd/etcd-key.pem \
>   endpoint health
https://192.168.1.73:2379 is healthy: successfully committed proposal: took = 7.365343ms
https://192.168.1.72:2379 is healthy: successfully committed proposal: took = 19.778578ms

```



查看etcd集群成员

```shell
root@master:~/kubernetes/service# ETCDCTL_API=3 etcdctl   --endpoints=https://192.168.1.73:2379   --cacert=/etc/kubernetes/ca/ca.pem   --cert=/etc/kubernetes/ca/etcd/etcd.pem   --key=/etc/kubernetes/ca/etcd/etcd-key.pem   member list
5c81b5ea448e2eb, started, 192.168.1.72, https://192.168.1.72:2380, https://192.168.1.72:2379
c39c45ea12ff2451, started, 192.168.1.73, https://192.168.1.73:2380, https://192.168.1.73:2379

```

查看k8s存储etcd的数据

ETCDCTL_API=3 etcdctl   --endpoints=https://192.168.1.72:2379,https://192.168.1.73:2379,https://192.168.1.74:2379    --cacert=/etc/kubernetes/ca/ca.pem   --cert=/etc/kubernetes/ca/etcd/etcd.pem   --key=/etc/kubernetes/ca/etcd/etcd-key.pem get / --prefix --keys-only

