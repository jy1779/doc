kubectl 指令

回滚

```shell
kubectl rollout undo deploy kubernetes-bootcamp
```

添加标签

```shell
kubectl label node k8s-node1 label=label
```

删除标签

```shell
kubectl label node k8s-node1 label-
```

