# 配置阿里云钉钉报警

1.  准备脚本
- 获取token: 钉钉团队-群机器人-复制token
- 钉钉开发者中心：https://open-doc.dingtalk.com/docs/doc.htm?spm=a219a.7629140.0.0.TwwXP7&treeId=257&articleId=105735&docType=1
```
$ grep alertscripts /etc/zabbix/zabbix_server.conf 
# AlertScriptsPath=${datadir}/zabbix/alertscripts
AlertScriptsPath=/usr/lib/zabbix/alertscripts

$ cat /usr/lib/zabbix/alertscripts/dingding.py 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import urllib3
import json
import sys
http = urllib3.PoolManager()
token  = "https://oapi.dingtalk.com/robot/send?access_token=e40d4908101336542cd45ae64ced1dce9a46ad7eda686833f6f6041c83a7a4a5"
head = {'Content-Type':'application/json'}
message = sys.argv[1]
text = '>%s' %(message)
data = {
        "msgtype": "markdown",
        "markdown": {
            "title": "监控小钉报告",
            "text": text
        } 
}
encode_data = json.dumps(data).encode('utf-8')
r = http.request(
        'POST',
        token,
        body = encode_data,
        headers = head
)
```
2.  配置Media types  
![dingding](https://raw.githubusercontent.com/jy1779/doc/master/image/zabbix/dingding1.png "配置Media types")  
3.  配置用户选择Media types  
![dingding](https://raw.githubusercontent.com/jy1779/doc/master/image/zabbix/dingding2.png "配置用户选择Media types")  
4.  配置触发器,触发后的action
![dingding](https://raw.githubusercontent.com/jy1779/doc/master/image/zabbix/dingding2.png "配置触发器,出发后的action") 
![dingding](https://raw.githubusercontent.com/jy1779/doc/master/image/zabbix/dingding_action2.png "配置触发器,出发后的action") 
![dingding](https://raw.githubusercontent.com/jy1779/doc/master/image/zabbix/dingding_action3.png "配置触发器,出发后的action") 

```
报警信息:
#### 服务器报警：
#### 告警主机：{HOSTNAME1}
#### 告警IP： {HOST.IP}
#### 告警时间：{EVENT.DATE} {EVENT.TIME}
#### 告警等级：{TRIGGER.SEVERITY}
#### 触发名称： {TRIGGER.NAME}
#### 告警项目：{TRIGGER.KEY1}
#### 问题详情：{ITEM.NAME}：{ITEM.VALUE}
#### 当前状态：{TRIGGER.STATUS}：{ITEM.VALUE1}
#### 事件ID：{EVENT.ID}
#### 事件状态：{EVENT.STATUS}
```

```
恢复信息：
#### 服务器恢复：
#### 告警主机：{HOSTNAME1}
#### 告警主机IP：{HOST.IP}
#### 告警时间：{EVENT.DATE} {EVENT.TIME}
#### 告警等级：{TRIGGER.SEVERITY}
#### 告警信息：{TRIGGER.NAME}
#### 告警项目：{TRIGGER.KEY1}
#### 问题详情：{ITEM.NAME}:{ITEM.VALUE}
#### 当前状态：{TRIGGER.STATUS}:{ITEM.VALUE1}
#### 事件ID：{EVENT.ID}
#### 事件状态：{EVENT.STATUS}
```
