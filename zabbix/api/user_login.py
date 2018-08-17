import urllib3
import json
http = urllib3.PoolManager()

data = {
    "jsonrpc": "2.0",
    "method": "user.login",
    "params": {
        "user": "Admin",
        "password": "zabbix"
    },
    "id": 1
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
