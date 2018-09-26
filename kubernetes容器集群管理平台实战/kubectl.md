# kubectl

> 默认情况下kubectl连接本地apiserver：127.0.0.1:8080
>
> ```shell
> root@k8s-master:~# kubectl -s 127.0.0.1:8080 get node
> NAME           STATUS    ROLES     AGE       VERSION
> 192.168.1.69   Ready     <none>    5h        v1.9.0
> ```

配置kubectl远程客户端

```shell
#拷贝kubectl指令
root@k8s-master:~# scp /usr/bin/kubectl 192.168.1.69:/usr/bin/kubectl
kubectl                                                                                                                                                    100%   53MB  13.2MB/s   00:04    
#拷贝证书
root@k8s-master:~/ssl# scp admin*.pem 192.168.1.69:/root/ssl/
admin-key.pem                                                                                                                                              100% 1675     1.6KB/s   00:00    
admin.pem                                                                                                                                                  100% 1407     1.4KB/s   00:00    
root@k8s-master:~/ssl# scp ca.pem  192.168.1.69:/root/ssl/
ca.pem                                                                                                                                                     100% 1363     1.3KB/s   00:00  
# 设置集群项中名为kubernetes的apiserver地址与根证书
kubectl config set-cluster kubernetes --server=https://192.168.1.67:6443 --certificate-authority=ca.pem
# 设置用户项中cluster-admin用户证书认证字段
kubectl config set-credentials cluster-admin --certificate-authority=ca.pem --client-key=admin-key.pem --client-certificate=admin.pem
# 设置环境项中名为default的默认集群和用户
kubectl config set-context default --cluster=kubernetes --user=cluster-admin
# 设置默认环境项为default
kubectl config use-context default
# 生成该文件
root@k8s-node1:~/ssl# cat /root/.kube/config 
apiVersion: v1
clusters:
- cluster:
    certificate-authority: /root/ssl/ca.pem
    server: https://192.168.1.67:6443
  name: kubernetes
contexts:
- context:
    cluster: kubernetes
    user: cluster-admin
  name: default
current-context: default
kind: Config
preferences: {}
users:
- name: cluster-admin
  user:
    client-certificate: /root/ssl/admin.pem
    client-key: /root/ssl/admin-key.pem
# 执行kubectl命令
root@k8s-node1:~/ssl# kubectl get node
NAME           STATUS    ROLES     AGE       VERSION
192.168.1.69   Ready     <none>    5h        v1.9.0
#可以将kubectl和/root/.kube/config及admin-key.pem  admin.pem  ca.pem证书打包，放到其他服务器也依旧可以远程管理集群
```

