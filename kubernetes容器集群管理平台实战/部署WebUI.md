# 部署WebUI

 dashboard-rbac.yaml 文件

```yaml
root@k8s-master:~/ui# cat dashboard-rbac.yaml 
apiVersion: v1
kind: ServiceAccount
metadata:
  labels:
    k8s-app: kubernetes-dashboard
    addonmanager.kubernetes.io/mode: Reconcile
  name: kubernetes-dashboard
  namespace: kube-system
---
kind: ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1beta1
metadata:
  name: kubernetes-dashboard-minimal
  namespace: kube-system
  labels:
    k8s-app: kubernetes-dashboard
    addonmanager.kubernetes.io/mode: Reconcile
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
  - kind: ServiceAccount
    name: kubernetes-dashboard
    namespace: kube-system
```

创建rbac

```shell
root@k8s-master:~/ui# kubectl create -f dashboard-rbac.yaml 
serviceaccount/kubernetes-dashboard created
clusterrolebinding.rbac.authorization.k8s.io/kubernetes-dashboard-minimal created
```

dashboard-deployment.yaml文件

```yaml
root@k8s-master:~/ui# cat dashboard-deployment.yaml
apiVersion: apps/v1beta2
kind: Deployment
metadata:
  name: kubernetes-dashboard
  namespace: kube-system
  labels:
    k8s-app: kubernetes-dashboard
    kubernetes.io/cluster-service: "true"
    addonmanager.kubernetes.io/mode: Reconcile
spec:
  selector:
    matchLabels:
      k8s-app: kubernetes-dashboard
  template:
    metadata:
      labels:
        k8s-app: kubernetes-dashboard
      annotations:
        scheduler.alpha.kubernetes.io/critical-pod: ''
    spec:
      serviceAccountName: kubernetes-dashboard
      containers:
      - name: kubernetes-dashboard
        image: registry.cn-hangzhou.aliyuncs.com/google_containers/kubernetes-dashboard-amd64:v1.7.1
        resources:
          limits:
            cpu: 100m
            memory: 300Mi
          requests:
            cpu: 100m
            memory: 100Mi
        ports:
        - containerPort: 9090
          protocol: TCP
        livenessProbe:
          httpGet:
            scheme: HTTP
            path: /
            port: 9090
          initialDelaySeconds: 30
          timeoutSeconds: 30
      tolerations:
      - key: "CriticalAddonsOnly"
        operator: "Exists"

```

创建dashboard-deployment

```shell
root@k8s-master:~/ui# kubectl create -f dashboard-deployment.yaml
```

dashboard-service.yaml 

```yaml
root@k8s-master:~/ui# cat dashboard-service.yaml 
apiVersion: v1
kind: Service
metadata:
  name: kubernetes-dashboard
  namespace: kube-system
  labels:
    k8s-app: kubernetes-dashboard
    kubernetes.io/cluster-service: "true"
    addonmanager.kubernetes.io/mode: Reconcile
spec:
  type: NodePort
  selector:
    k8s-app: kubernetes-dashboard
  ports:
  - port: 80
    targetPort: 9090

```

创建dashboard-service

```shell
root@k8s-master:~/ui# kubectl create -f dashboard-service.yaml 
```

访问dashboard

```shell
root@k8s-master:~/ui# kubectl -n kube-system get service
NAME                   TYPE       CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
kubernetes-dashboard   NodePort   10.10.10.159   <none>        80:13639/TCP   5m
#浏览器访问：192.168.69:13639
```

