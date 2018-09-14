# Service （服务）

Service也是kubernetes里的最核心的资源对象之一，Kuberneter里的每一个Service其实就是“微服务”

定义一个service:

```shell
apiVersion: v1
kind: Service
metadata:
  name: zeno-basic-service
spec:
  selector:
    app: zeno-basic   #选择定义该标签的pod
  ports:
  - protocol: TCP
    port: 8182    #Service 端口
    targetPort: 8182 #Pod端口
```

定义一个多端口的service，且设置NodePort

```shell
apiVersion: v1
kind: Service
metadata:
  name: zeno-elasticsearch-service
spec:
  selector:
    app: zeno-elasticsearch
  ports:
  - protocol: TCP
    name: port1
    port: 9200
    targetPort: 9200
    nodePort: 9200
  - protocol: TCP
    name: port2
    port: 9300
    targetPort: 9300
    nodePort: 9300  #nodePort端口，不指定则为随机端口
  type: NodePort
```



