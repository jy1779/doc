# 部署flannel网络

Overlay Network：覆盖网络，在基础网络上叠加的一种虚拟网络技术模式，该网络中的主机通过虚拟链路连接起来。
VXLAN：将源数据包封装到UDP中，并使用基础网络的IP/MAC作为外层报文头进行封装，然后在以太网上传输，到达目的地后由隧道端点解封装并将数据发送给目标地址。
Flannel：是Overlay网络的一种，也是将源数据包封装在另一种网络包里面进行路由转发和通信，目前已经支持UDP、VXLAN、AWS VPC和GCE路由等数据转发方式。
多主机容器网络通信其他主流方案：隧道方案（Weave、OpenvSwitch ），路由方案（Calico）等。

```shell
root@k8s-master:~# tar xf flannel-v0.9.1-linux-amd64.tar.gz
#拷贝到节点
root@k8s-master:~# scp flanneld mk-docker-opts.sh 192.168.1.69:/opt/kubernetes/bin/
flanneld                                                                                                                                                   100%   33MB  32.9MB/s   00:01    
mk-docker-opts.sh                                                                                                                                          100% 2139     2.1KB/s   00:00  
#向etcd里面添加flannel网段信息
root@k8s-master:~# /opt/kubernetes/bin/etcdctl \
--ca-file=ca.pem --cert-file=server.pem --key-file=server-key.pem \
--endpoints="https://192.168.1.67:2379,https://192.168.1.69:2379" \
set /coreos.com/network/config '{ "Network": "172.17.0.0/16", "Backend": {"Type": "vxlan"}}'
#返回
{ "Network": "172.17.0.0/16", "Backend": {"Type": "vxlan"}}

```

### k8s-node1部署flannel

```shell

#配置flannel启动参数
root@k8s-node1:/opt/kubernetes/ssl# cat  /opt/kubernetes/cfg/flanneld
FLANNEL_OPTIONS="--etcd-endpoints=https://192.168.1.67:2379,https://192.168.1.69:2379 -etcd-cafile=/opt/kubernetes/ssl/ca.pem -etcd-certfile=/opt/kubernetes/ssl/server.pem -etcd-keyfile=/opt/kubernetes/ssl/server-key.pem"
#配置flannel启动文件
root@k8s-node1:~# cat  /lib/systemd/system/flanneld.service
[Unit]
Description=Flanneld overlay address etcd agent
After=network-online.target network.target
Before=docker.service

[Service]
Type=notify
EnvironmentFile=/opt/kubernetes/cfg/flanneld
ExecStart=/opt/kubernetes/bin/flanneld --ip-masq $FLANNEL_OPTIONS
ExecStartPost=/opt/kubernetes/bin/mk-docker-opts.sh -k DOCKER_NETWORK_OPTIONS -d /run/flannel/subnet.env
Restart=on-failure

[Install]
WantedBy=multi-user.target
#创建并启动flannel服务
systemctl enable flanneld
systemctl start flanneld
#查看IP
root@k8s-node1:~# ip a |grep flannel
4: flannel.1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1450 qdisc noqueue state UNKNOWN group default 
    inet 172.17.13.0/32 scope global flannel.1
#flannel启动后生成文件
root@k8s-node1:~# cat /run/flannel/subnet.env 
DOCKER_OPT_BIP="--bip=172.17.13.1/24"
DOCKER_OPT_IPMASQ="--ip-masq=false"
DOCKER_OPT_MTU="--mtu=1450"
DOCKER_NETWORK_OPTIONS=" --bip=172.17.13.1/24 --ip-masq=false --mtu=1450"
#修改docker.servier启动文件
root@k8s-node1:~# grep ExecStart -B 1 /lib/systemd/system/docker.service 
EnvironmentFile=/run/flannel/subnet.env
ExecStart=/usr/bin/dockerd -H fd:// $DOCKER_NETWORK_OPTIONS
#重启docker
root@k8s-node1:~# systemctl daemon-reload
root@k8s-node1:~# service docker restart


```

