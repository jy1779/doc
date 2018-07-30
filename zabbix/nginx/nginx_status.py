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