# Secret

1.创建集群管理员

```shell
root@master:~/kubernetes/token# cat admin-role.yaml 
kind: ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1beta1
metadata:
  name: admin
  annotations:
    rbac.authorization.kubernetes.io/autoupdate: "true"
roleRef:
  kind: ClusterRole
  name: cluster-admin
  apiGroup: rbac.authorization.k8s.io
subjects:
- kind: ServiceAccount
  name: admin
  namespace: kube-system
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: admin
  namespace: kube-system
  labels:
    kubernetes.io/cluster-service: "true"
    addonmanager.kubernetes.io/mode: Reconcile
root@master:~/kubernetes/token# kubectl apply -f admin-role.yaml 
clusterrolebinding "admin" configured
serviceaccount "admin" created

```

2.查看令牌

```shell
root@master:~/kubernetes/token# kubectl -n kube-system  get secret admin-token-sdpxz -o jsonpath={.data.token}| base64 -d
eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJrdWJlLXN5c3RlbSIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VjcmV0Lm5hbWUiOiJhZG1pbi10b2tlbi1zZHB4eiIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50Lm5hbWUiOiJhZG1pbiIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50LnVpZCI6IjBiNzkzODlhLWNjMzAtMTFlOC1hYjE4LTAwMGMyOTYzYWFjYyIsInN1YiI6InN5c3RlbTpzZXJ2aWNlYWNjb3VudDprdWJlLXN5c3RlbTphZG1pbiJ9.g-J9hV2dP2O679QvSfX5ANnO3cwVcYU31UVj_WQXmg52dPCLtX9Y5UcFh9oZaw6r6zrgFvJuk3JEMfvCGEQSgfxp2JWMaS307mFXnqBbBK4VwWWHHbGg4b_BHO7O18uBpLplKjYPZtnkeWBj7Bgj-DuNcOrpBvZWXJrXFf4xLMfJYomMhpRIWIkGX_Vef504bw4NoGaJLMPGd9aUyjTkMr78vOdK-C9Vq_h5Aaf01PSlA_JJ0adLzZgFGrj_mGeA6m8PdQ93b2BAf7PY9vkvrgB_1YaursNmZ0XhxVRhSDZ3V6SuUjoTN8SmcTVd5BkcVVY_AbwHFSxxHcHRQ0M_WQ
```

