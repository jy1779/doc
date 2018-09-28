# k8s添加新节点

1. 在master服务器上操作

2. master与node节点做免密登录

3. 准备执行shell命令的脚本，路径：/scripts/python/shell.py

   ```python
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
   ```

4. 创建目录：/root/kubernetes/add_node,以下内容

```shell
root@master:~/kubernetes# tree add_node/
add_node/
├── add_node.py   #新增node脚本
├── bootstrap.kubeconfig #在现有节点拷贝bootstrap.kubeconfig
├── config.properties    #准备config.properties
├── kube-proxy           #在现有节点拷贝kube-proxy证书
│   ├── kube-proxy.csr
│   ├── kube-proxy-csr.json
│   ├── kube-proxy-key.pem
│   └── kube-proxy.pem
└── kube-proxy.kubeconfig #在现有节点拷贝kube-proxy.kubeconfig

```

add_node.py脚本内容：

```python
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
      self.node.realtime_shell('docker pull registry.cn-hangzhou.aliyuncs.com/imooc/calico-node:v2.6.2')
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
```

5. 执行脚本

```shell
./add_node.py node03
```



