# Deployment（部署）

一个部署控制器提供声明更新Pod和 ReplicaSets。

您在Deployment对象中描述了所需的状态，Deployment控制器以受控速率将实际状态更改为所需状态。您可以定义“Deployment”以创建新的ReplicaSet，或者删除现有的部署并使用新的部署采用所有资源。

```shell
apiVersion: extensions/v1beta1
kind: Deployment
metadata:
  name: zeno-elasticsearch
spec:
  replicas: 1
  template:
    metadata:
      labels:
        app: zeno-elasticsearch
    spec:
      containers:
      - name: zeno-elasticsearch
        image: harbor.xwkj.local/com.zeno/elasticsearch:latest6
        ports:
          - name: port1
            containerPort: 9200
          - name: port2
            containerPort: 9300
        envFrom:
          - configMapRef:
              name: zeno-elasticsearch-configmap
        volumeMounts:
          - name: config
            mountPath: /usr/share/elasticsearch/config
          - name: data
            mountPath: /usr/share/elasticsearch/data
      volumes:
        - name: config
          nfs:
            server: 192.168.1.203
            path: /data/zeno/elasticsearch/config
        - name: data
          nfs:
            server: 192.168.1.203
            path: /data/zeno/elasticsearch/data
      nodeSelector:
        ip: 192.168.1.252
```

