master 创建pod

master报错：

Warning  FailedCreatePodSandBox  4s (x2 over 15s)  kubelet, 192.168.1.73  Failed create pod sandbox.

节点kubelet报错：

Oct 17 14:22:16 node01 kubelet[8012]: E1017 14:22:16.232787    8012 pod_workers.go:186] Error syncing pod 22edcefc-d1be-11e8-8c1f-000c2963aacc ("pod-nginx_default(22edcefc-d1be-11e8-8c1f-000c2963aacc)"), skipping: failed to "CreatePodSandbox" for "pod-nginx_default(22edcefc-d1be-11e8-8c1f-000c2963aacc)" with CreatePodSandboxError: "CreatePodSandbox for pod \"pod-nginx_default(22edcefc-d1be-11e8-8c1f-000c2963aacc)\" failed: rpc error: code = Unknown desc = failed pulling image \"registry.cn-hangzhou.aliyuncs.com/jonny/pause-amd64:3.0\": Error response from daemon: pull access denied for registry.cn-hangzhou.aliyuncs.com/jonny/pause-amd64, repository does not exist or may require 'docker login'"