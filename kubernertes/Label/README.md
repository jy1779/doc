# Label (标签)

Label是Kubernetes系统中另外一个核心概念。一个Label是一个key=value的键值对，其中key与value由用户自己定义指定。Label可以附加到各种资源对象上，例如Node、Pod、Service、RC等，一个资源对象可以定义任意数量的Label，同一个Label也可以被添加到任意数量的资源对象上去，Lebel通常在资源对象定义时确定，也可以在对象创建后动态添加或删除。

添加标签

```shell
kubectl label node k8s-node1 label=label
```

删除标签

```shell
kubectl label node k8s-node1 label-
```

