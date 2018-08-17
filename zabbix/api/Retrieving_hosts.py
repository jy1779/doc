#检索主机
import urllib3
import json
http = urllib3.PoolManager()

data = {
    "jsonrpc": "2.0",
    "method": "host.get",
    "params": {
        "output": [
            "hostid",
            "host"
        ],
        "selectInterfaces": [
            "interfaceid",
            "ip"
        ]
    },
    "id": 2,
    "auth": "4885d93ccdff259223239f789d1ad3e0"
}
encode_data = json.dumps(data).encode('utf-8')
request = http.request(
    'GET',
    'http://192.168.1.202/zabbix/api_jsonrpc.php',
    headers = {'Content-Type':'application/json-rpc'},
    body = encode_data
)
print(request.status)
print(request.data)
