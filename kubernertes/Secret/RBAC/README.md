# RBAC概述

> 基于角色的访问控制（“RBAC”）使用“rbac.authorization.k8s.io”API 组来实现授权控制，允许管理员通过Kubernetes API动态配置策略。
>
> 参考：http://docs.kubernetes.org.cn/148.html

### Role

> Role是一系列的权限的集合
>
> role包含了一套表示一组权限的规则
>
> Role只能授予单个namespace中资源的访问权限，如下：
>
> Role示例：

```shell
kind: Role
apiVersion: rbac.authorization.k8s.io/v1beta1
metadata:
  namespace: default
  name: pod-reader
rules:
- apiGroups: [""] # "" indicates the core API group
  resources: ["pods"]
  verbs: ["get", "watch", "list"]
```

### ClusterRole

> ClusterRole授权 >= Role授予（与Role类似）但ClusterRole属于集群级别对象：
>
> - 集群范围（cluster-scoped）的资源访问控制（如：节点访问权限）
> - 非资源类型（如“/ healthz”）
> - 所有namespaces 中的namespaced 资源（如 pod）
>
> ClusterRole示例：

```shell
kind: ClusterRole
apiVersion: rbac.authorization.k8s.io/v1beta1
metadata:
  # "namespace" omitted since ClusterRoles are not namespaced
  name: secret-reader
rules:
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get", "watch", "list"]
```

### RoleBinding和ClusterRoleBinding

> RoleBinding是将Role中定义的权限授予给用户或用户组。它包含一个subjects列表(users，groups ，service accounts)，并引用该Role。RoleBinding在某个namespace 内授权，ClusterRoleBinding适用在集群范围内使用。
>
> RoleBinding可以引用相同namespace下定义的Role。以下的RoleBinding在“default”namespace中将“pod-reader”Role授予用户“jane”。将允许“jane”在“default”namespace中读取pod权限。

```shell
# This role binding allows "jane" to read pods in the "default" namespace.
kind: RoleBinding
apiVersion: rbac.authorization.k8s.io/v1beta1
metadata:
  name: read-pods
  namespace: default
subjects:
- kind: User
  name: jane
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

> RoleBinding还可以参考ClusterRole。将允许管理员为整个集群定义一组通用Role，然后在不同namespace中使用RoleBinding引用。

```shell
# This role binding allows "dave" to read secrets in the "development" namespace.
kind: RoleBinding
apiVersion: rbac.authorization.k8s.io/v1beta1
metadata:
  name: read-secrets
  namespace: development # This only grants permissions within the "development" namespace.
subjects:
- kind: User
  name: dave
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: secret-reader
  apiGroup: rbac.authorization.k8s.io
```

> 最后，ClusterRoleBinding可以用于集群中所有命名空间中授予权限。以下ClusterRoleBinding允许组“manager”中的任何用户在任何命名空间中读取secrets。

```shell
# This cluster role binding allows anyone in the "manager" group to read secrets in any namespace.
kind: ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1beta1
metadata:
  name: read-secrets-global
subjects:
- kind: Group
  name: manager
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: secret-reader
  apiGroup: rbac.authorization.k8s.io
```

