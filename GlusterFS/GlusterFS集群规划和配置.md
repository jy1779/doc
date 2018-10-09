# GluserFS集群规划和配置

简单的集群使用

| 计算机名称 | IP            | 角色  |
| ---------- | ------------- | ----- |
| ubunut2    | 192.168.0.182 | 节点1 |
| ubuntu3    | 192.168.1.131 | 节点2 |

```shell
#在两个节点创建以下目录
mkdir -p /export/sdb1/brick 
#在节点1添加节点2到集群，节点1为当前节点
root@ubuntu2:/data# gluster peer status
Number of Peers: 0
root@ubuntu2:/data# gluster peer probe 192.168.1.131
peer probe: success. 
root@ubuntu2:/data# gluster peer status
Number of Peers: 1

Hostname: 192.168.1.131
Uuid: 66092a40-4b96-45de-8d6e-f9a3a1efbb04
State: Peer in Cluster (Connected)

#创建volume 卷
#replica 2 说明至少保留两份完整副本
root@ubuntu2:/data# gluster volume create gv1 replica 2 192.168.0.182:/export/sdb1/brick 192.168.1.131:/export/sdb1/brick
#查看volume情况
root@ubuntu2:/data# gluster volume info
 
Volume Name: gv1
Type: Replicate
Volume ID: 54cd9ac4-a1ce-4996-b252-5fd3ef9534ca
Status: Created
Number of Bricks: 1 x 2 = 2
Transport-type: tcp
Bricks:
Brick1: 192.168.0.182:/export/sdb1/brick
Brick2: 192.168.1.131:/export/sdb1/brick
Options Reconfigured:
performance.readdir-ahead: on
#启动volume gv1卷
root@ubuntu2:/data# gluster volume start gv1
#挂载gv1卷
root@ubuntu3:~# mount -t glusterfs 192.168.0.182:/gv1 /mnt/data1
#测试，进入挂载目录创建文件
root@ubuntu3:~# cd /mnt/data1
root@ubuntu3:/mnt/data1# ls
root@ubuntu3:/mnt/data1# touch 1
#查看两个节点的目录都已有文件
root@ubuntu3:/mnt/data1# ls /export/sdb1/brick/
1
root@ubuntu2:/data# ls /export/sdb1/brick/
1



```

