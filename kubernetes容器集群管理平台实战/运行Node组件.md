# 运行Node组件

```shell
#解压node.zip
root@k8s-node1:~# unzip node.zip
root@k8s-node1:~# mv kubelet kube-proxy /opt/kubernetes/bin/
root@k8s-node1:~# chmod +x kubelet.sh 
root@k8s-node1:~# chmod +x proxy.sh 

#在master将kubeconfig文件复制到node
root@k8s-master:~/ssl# scp *.kubeconfig 192.168.1.69:/opt/kubernetes/cfg/
bootstrap.kubeconfig                                                                                                                                       100% 2174     2.1KB/s   00:00    
kube-proxy.kubeconfig                                                                                                                                      100% 6280     6.1KB/s   00:00   
#在master创建该用户
root@k8s-master:~# kubectl create clusterrolebinding kubelet-bootstrap --clusterrole=system:node-bootstrapper --user=kubelet-bootstrap
clusterrolebinding.rbac.authorization.k8s.io/kubelet-bootstrap created

#启动kubelet
#执行脚本
root@k8s-node1:~# cat ./kubelet.sh 
#!/bin/bash

NODE_ADDRESS=${1:-"192.168.1.196"}
DNS_SERVER_IP=${2:-"10.10.10.2"}

cat <<EOF >/opt/kubernetes/cfg/kubelet

KUBELET_OPTS="--logtostderr=true \\
--v=4 \\
--address=${NODE_ADDRESS} \\
--hostname-override=${NODE_ADDRESS} \\
--kubeconfig=/opt/kubernetes/cfg/kubelet.kubeconfig \\
--experimental-bootstrap-kubeconfig=/opt/kubernetes/cfg/bootstrap.kubeconfig \\
--cert-dir=/opt/kubernetes/ssl \\
--allow-privileged=true \\
--cluster-dns=${DNS_SERVER_IP} \\
--cluster-domain=cluster.local \\
--fail-swap-on=false \\
--pod-infra-container-image=registry.cn-hangzhou.aliyuncs.com/google-containers/pause-amd64:3.0"

EOF

cat <<EOF >/lib/systemd/system/kubelet.service
[Unit]
Description=Kubernetes Kubelet
After=docker.service
Requires=docker.service

[Service]
EnvironmentFile=-/opt/kubernetes/cfg/kubelet
ExecStart=/opt/kubernetes/bin/kubelet \$KUBELET_OPTS
Restart=on-failure
KillMode=process

[Install]
WantedBy=multi-user.target
EOF

systemctl enable kubelet
systemctl start kubelet

root@k8s-node1:~# ./kubelet.sh 192.168.1.69 10.10.10.2
#在master同意kubelet的证书请求
root@k8s-master:~# kubectl get csr
NAME                                                   AGE       REQUESTOR           CONDITION
node-csr-MN84tPtIZycIo9XUHidU0wRounNRIqFB9qEhDtz0c3o   4m        kubelet-bootstrap   Pending

root@k8s-master:~# kubectl certificate approve node-csr-MN84tPtIZycIo9XUHidU0wRounNRIqFB9qEhDtz0c3o
certificatesigningrequest.certificates.k8s.io/node-csr-MN84tPtIZycIo9XUHidU0wRounNRIqFB9qEhDtz0c3o approved
root@k8s-master:~# kubectl get csr
NAME                                                   AGE       REQUESTOR           CONDITION
node-csr-MN84tPtIZycIo9XUHidU0wRounNRIqFB9qEhDtz0c3o   6m        kubelet-bootstrap   Approved,Issued
#在node下查看该文件
root@k8s-node1:~# ls  /opt/kubernetes/cfg/kubelet.kubeconfig
/opt/kubernetes/cfg/kubelet.kubeconfig
#查看node的证书目录，多出以下证书
#当启动kubelet就会创建kubelet证书
kubelet.crt  kubelet.key
#当k8s集群同意该证书请求就会签发下面的两个证书
kubelet-client.crt  kubelet-client.key  

root@k8s-node1:~# ls /opt/kubernetes/ssl/
ca.pem  kubelet-client.crt  kubelet-client.key  kubelet.crt  kubelet.key  server-key.pem  server.pem

#启动kube-proxy
root@k8s-master:~/ssl# scp kube-proxy.pem 192.168.1.69:/opt/kubernetes/ssl/
kube-proxy.pem                                                                                                                                             100% 1407     1.4KB/s   00:00    
root@k8s-master:~/ssl# scp kube-proxy-key.pem 192.168.1.69:/opt/kubernetes/ssl/
kube-proxy-key.pem                                                                                                                                         100% 1675     1.6KB/s   00:00   
root@k8s-node1:~# cat proxy.sh 
#!/bin/bash

NODE_ADDRESS=${1:-"192.168.1.200"}

cat <<EOF >/opt/kubernetes/cfg/kube-proxy

KUBE_PROXY_OPTS="--logtostderr=true \
--v=4 \
--hostname-override=${NODE_ADDRESS} \
--kubeconfig=/opt/kubernetes/cfg/kube-proxy.kubeconfig"

EOF

cat <<EOF >/lib/systemd/system/kube-proxy.service
[Unit]
Description=Kubernetes Proxy
After=network.target

[Service]
EnvironmentFile=-/opt/kubernetes/cfg/kube-proxy
ExecStart=/opt/kubernetes/bin/kube-proxy \$KUBE_PROXY_OPTS
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

systemctl enable kube-proxy
systemctl start kube-proxy
#执行脚本
root@k8s-node1:~# ./proxy.sh 192.168.1.69
root@k8s-node1:~# cat /opt/kubernetes/cfg/kube-proxy

KUBE_PROXY_OPTS="--logtostderr=true --v=4 --hostname-override=192.168.1.69 --kubeconfig=/opt/kubernetes/cfg/kube-proxy.kubeconfig"
root@k8s-node1:~# cat /lib/systemd/system/kube-proxy.service 
[Unit]
Description=Kubernetes Proxy
After=network.target

[Service]
EnvironmentFile=-/opt/kubernetes/cfg/kube-proxy
ExecStart=/opt/kubernetes/bin/kube-proxy $KUBE_PROXY_OPTS
Restart=on-failure

[Install]
WantedBy=multi-user.target

```

