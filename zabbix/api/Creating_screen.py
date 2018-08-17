#创建屏幕
import urllib3
import json
http = urllib3.PoolManager()

data = {
    "jsonrpc": "2.0",
    "method": "screen.create",
    "params": {
        "name": "Graphs",
        "hsize": 3,
        "vsize": 2,
        "screenitems": [
            {
                "resourcetype": 0,
                "resourceid": "612",
                "rowspan": 0,
                "colspan": 0,
                "x": 0,
                "y": 0
            }
        ]
    },
    "id": 1,
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
