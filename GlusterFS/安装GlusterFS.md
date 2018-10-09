# 安装GlusterFS

- 软件下载
  - http://download.gluster.org/pub/gluster/glusterfs/
- apt-get 安装方式：

```shell
root@ubuntu2:~# apt-get install software-properties-common
root@ubuntu2:~# add-apt-repository ppa:gluster/glusterfs-3.8
root@ubuntu2:~# apt-get update
root@ubuntu2:~# apt-get install glusterfs-server
root@ubuntu2:~# service glusterfs-server status
● glusterfs-server.service - LSB: GlusterFS server
   Loaded: loaded (/etc/init.d/glusterfs-server; bad; vendor preset: enabled)
   Active: active (running) since Tue 2018-10-09 10:02:17 CST; 28s ago
     Docs: man:systemd-sysv-generator(8)
   CGroup: /system.slice/glusterfs-server.service
           └─30811 /usr/sbin/glusterd -p /var/run/glusterd.pid
#创建gluster volume卷
root@ubuntu2:~# gluster volume create gv0 192.168.0.182:/data/brick1 192.168.0.182:/data/brick2 force
#启动gluster volume卷
root@ubuntu2:~# gluster volume start gv0
#挂载gluster volume卷
root@ubuntu2:~# mount -t glusterfs 192.168.0.182:/gv0 /mnt
WARNING: getfattr not found, certain checks will be skipped..
#如提示以上警告，原因： attr是一个用于XFS文件系统对象上的扩展属性的命令
#解决方法：安装该命令，执行：
root@ubuntu2:~# apt-get install attr
root@ubuntu2:~# df -h|grep gv0
192.168.0.182:/gv0             37G  8.8G   26G  26% /mnt
#测试
root@ubuntu2:/data# ls /mnt/
root@ubuntu2:/data# touch /mnt/1
root@ubuntu2:/data# ls brick1/
1
root@ubuntu2:/data# ls brick2/
root@ubuntu2:/data# touch /mnt/2
root@ubuntu2:/data# ls brick2/
2
root@ubuntu2:/data# touch /mnt/3
root@ubuntu2:/data# ls brick2/
2  3
root@ubuntu2:/data# ls brick1/
1
root@ubuntu2:/data# touch /mnt/4
root@ubuntu2:/data# ls brick1/
1
root@ubuntu2:/data# ls brick2
2  3  4
root@ubuntu2:/data# touch /mnt/5
root@ubuntu2:/data# touch /mnt/6
root@ubuntu2:/data# ls brick2
2  3  4  6
root@ubuntu2:/data# ls brick1
1  5

#客户端需要安装glusterfs-client，才可以进行mount挂载
apt-get install glusterfs-client
centos： yum install glusterfs-fuse

```

