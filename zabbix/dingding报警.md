# 配置阿里云钉钉报警
1.  准备脚本

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
2.  