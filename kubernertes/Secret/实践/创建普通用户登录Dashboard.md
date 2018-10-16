# 创建普通用户登录Dashboard



```shell
#创建serviceaccount：test
root@master:~/kubernetes/token# kubectl create serviceaccount test -n test
serviceaccount "test" created
#创建role
root@master:~/kubernetes/token# cat test-role.yaml 
kind: Role
apiVersion: rbac.authorization.k8s.io/v1beta1
metadata:
  namespace: test  #只允许在test命名空间使用
  name: pod-reader
rules:
- apiGroups: [""] # "" indicates the core API group
  resources: ["pods", "pods/log"] #设置资源，pod及pod日志
  verbs: ["get", "list"] #操作权限
root@master:~/kubernetes/token# kubectl apply -f test-role.yaml  
#创建rolebinding，将用户与权限绑定
root@master:~/kubernetes/token# cat test-rolebinding.yaml 
kind: RoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: read-pods
  namespace: test
subjects:
- kind: ServiceAccount
  name: test
  namespace: test
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
root@master:~/kubernetes/token# kubectl apply -f test-rolebinding.yaml
#查看secrets
root@master:~/kubernetes/token# kubectl -n test get secrets|grep test
test-token-fp9fc      kubernetes.io/service-account-token   3         5m
#查看token,复制token，使用令牌，即可登录Dashboard，
root@master:~/kubernetes/token# kubectl -n test describe  secrets test-token-fp9fc 
Name:         test-token-fp9fc
Namespace:    test
Labels:       <none>
Annotations:  kubernetes.io/service-account.name=test
              kubernetes.io/service-account.uid=ce19c783-cc62-11e8-ab18-000c2963aacc

Type:  kubernetes.io/service-account-token

Data
====
ca.crt:     1346 bytes
namespace:  4 bytes
token:      eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJ0ZXN0Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZWNyZXQubmFtZSI6InRlc3QtdG9rZW4tZnA5ZmMiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC5uYW1lIjoidGVzdCIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50LnVpZCI6ImNlMTljNzgzLWNjNjItMTFlOC1hYjE4LTAwMGMyOTYzYWFjYyIsInN1YiI6InN5c3RlbTpzZXJ2aWNlYWNjb3VudDp0ZXN0OnRlc3QifQ.nGf-gvkYIojKRFzTDPWrOIWDzJ3A20qD6VqPp3QkQoXj2LpKhnvzxD6H4Yyw-QdJOjBTL8hFkEMKt0LxQqkuslK8CrlgpfypFxxkeX4fuAXbS3qyrXc46cKssdk1y4Ds2v6ruf4KFSEgkaM7Pz_CucVViihHUMjxMBWB-lygNWaRJiIImju_AUVwgt1CDF-NRqWYZdMNlwI7Lv-qjX-6VfRoyNYTUAvR0b6jozp11T-lMTU9XBGSU8xoLzTjPwW7xyUMvKC3OqeuWghEssftan2EOqRafKaNiIqONyi-hlZb0VmkfLymdJsz5b8aXGFr3PU6s40ENrcOYvaReMJS8A

```

