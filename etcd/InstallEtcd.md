Install etcd 3.2

下载二进制：https://github.com/etcd-io/etcd/releases/

配置启动文件

```shell
root@om:~# cat /lib/systemd/system/etcd.service 
[Unit]
Description=Etcd Server
After=network.target
After=network-online.target
Wants=network-online.target
Documentation=https://github.com/coreos

[Service]
Type=notify
WorkingDirectory=/var/lib/etcd/
ExecStart=/usr/local/sbin/etcd \
  --name=192.168.1.55 \
  --listen-client-urls=http://192.168.1.55:2379,http://127.0.0.1:2379 \
  --advertise-client-urls=http://192.168.1.55:2379 \
  --data-dir=/var/lib/etcd \
  --listen-peer-urls=http://192.168.1.55:2380 \
  --initial-advertise-peer-urls=http://192.168.1.55:2380 \
Restart=on-failure
RestartSec=5
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
systemctl enable etcd.service #创建服务
service etcd start #启动服务
etcdctl put foo1 123  #设置key和value
```

