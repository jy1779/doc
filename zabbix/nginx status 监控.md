# nginx status 监控
1.  配置nginx status  
参考nginx官网：https://nginx.org/en/docs/http/ngx_http_stub_status_module.html
2.  准备脚本  
脚本说明：  
获取nginx status的值:  
active: 当前活动客户端连接数，包括Waiting连接数。  
accepts: 已接受的客户端连接总数。
handled: 处理的连接总数。通常，参数值与accepts 除非已达到某些资源限制（例如， worker_connections限制）相同。  
requests: 客户端请求的总数。  
Reading: nginx正在读取请求标头的当前连接数。  
Writing: nginx将响应写回客户端的当前连接数。  
Waiting: 当前等待请求的空闲客户端连接数。   
路径：/etc/zabbix/scripts/nginx_status.py 
```
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# luojiayi
import subprocess
import re
import sys
class Cmd(object):
    def onetime_shell(self,cmd):
        cmd = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
        cmd = cmd.communicate()
        cmd = cmd[0].decode()
        return cmd
    def realtime_shell(self,cmd):
        cmd = subprocess.call(cmd, shell=True)
        return cmd
class Main(object):
    def __init__(self):
        self.argv = sys.argv[1]
        self.cmd = Cmd()
        self.nginx_status_url = 'http://10.251.226.110/xw_NginxStatus/'
    def nginx_status(self):
        if self.argv == 'active':
           status = self.cmd.onetime_shell('curl -s %s |awk NR==1|awk \'{print $3}\'' %self.nginx_status_url).rstrip()
           return status
        elif self.argv == 'accepts':
           status = self.cmd.onetime_shell('curl -s %s |awk NR==3|awk \'{print $1}\'' %self.nginx_status_url).rstrip()
           return status
        elif self.argv == 'handled':
           status = self.cmd.onetime_shell('curl -s %s |awk NR==3|awk \'{print $2}\'' %self.nginx_status_url).rstrip()
           return status
        elif self.argv == 'requests':
           status = self.cmd.onetime_shell('curl -s %s |awk NR==3|awk \'{print $3}\'' %self.nginx_status_url).rstrip()
           return status
        elif self.argv == 'reading':
           status = self.cmd.onetime_shell('curl -s %s |awk NR==4|awk \'{print $2}\'' %self.nginx_status_url).rstrip()
           return status
        elif self.argv == 'writing':
           status = self.cmd.onetime_shell('curl -s %s |awk NR==4|awk \'{print $4}\'' %self.nginx_status_url).rstrip()
           return status
        elif self.argv == 'waiting':
           status = self.cmd.onetime_shell('curl -s %s |awk NR==4|awk \'{print $6}\'' %self.nginx_status_url).rstrip()
           return status
        elif self.argv == 'pid':
           status = self.cmd.onetime_shell('pidof nginx | wc -l').rstrip()
           return status
main = Main()
print(main.nginx_status())
```
3.  zabbix_agent配置文件：  
```
$ grep nginx_status /etc/zabbix/zabbix_agentd.conf
UserParameter=ngx_status[*],/etc/zabbix/scripts/nginx_status.py "$1"
```
