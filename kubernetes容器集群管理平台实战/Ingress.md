# Ingress

部署ingress-nginx

```shell
kubectl apply -f namespace.yaml 
kubectl apply -f default-backend.yaml 
kubectl apply -f tcp-services-configmap.yaml 
kubectl apply -f udp-services-configmap.yaml 
kubectl apply -f rbac.yaml
kubectl apply -f deployment.yaml

```



https

生成证书

1. 生成证书颁发机构

   ```shell
   root@master:~/kubernetes/service/https# cfssl print-defaults csr > ca-csr.json
   root@master:~/kubernetes/service/https# ls
   ca-csr.json
   root@master:~/kubernetes/service/https# cat ca-csr.json 
   {
       "CN": "example.net",
       "hosts": [
           "example.net",
           "www.example.net"
       ],
       "key": {
           "algo": "ecdsa",
           "size": 256
       },
       "names": [
           {
               "C": "US",
               "L": "CA",
               "ST": "San Francisco"
           }
       ]
   }
   #修改ca-csr.json文件
   root@master:~/kubernetes/service/https# cat ca-csr.json 
   {
       "CN": "jonny",
       "key": {
           "algo": "rsa",
           "size": 2048
       },
       "names": [
           {
               "C": "CN",
               "L": "Shenzhen",
               "ST": "Shenzhen"
           }
       ]
   }
   
   ```

2. 生成config配置模板

   ```shell
   root@master:~/kubernetes/service/https# cfssl print-defaults config > ca-config.json
   #仅测试用，默认即可
   root@master:~/kubernetes/service/https# cat  ca-config.json 
   {
       "signing": {
           "default": {
               "expiry": "168h"
           },
           "profiles": {
               "www": {
                   "expiry": "8760h",
                   "usages": [
                       "signing",
                       "key encipherment",
                       "server auth"
                   ]
               },
               "client": {
                   "expiry": "8760h",
                   "usages": [
                       "signing",
                       "key encipherment",
                       "client auth"
                   ]
               }
           }
       }
   }
   
   ```

3. 初始化ca机构

   ```shell
   root@master:~/kubernetes/service/https# cfssl gencert --initca ca-csr.json |cfssljson -bare ca - 
   2018/10/08 10:42:06 [INFO] generating a new CA key and certificate from CSR
   2018/10/08 10:42:06 [INFO] generate received request
   2018/10/08 10:42:06 [INFO] received CSR
   2018/10/08 10:42:06 [INFO] generating key: rsa-2048
   2018/10/08 10:42:06 [INFO] encoded CSR
   2018/10/08 10:42:06 [INFO] signed certificate with serial number 166914532578938495892409344505207399412061864365
   root@master:~/kubernetes/service/https# ls
   ca-config.json  ca.csr  ca-csr.json  ca-key.pem  ca.pem
   
   ```

4. 为网站生成证书

   ```shell
   #创建模板
   root@master:~/kubernetes/service/https# cfssl print-defaults csr > service-csr.json
   root@master:~/kubernetes/service/https# cat  service-csr.json  #修改默认json文件
   {
       "CN": "www.jonny.com",  #写网站域名
       "key": {
           "algo": "rsa",
           "size": 2048
       },
       "names": [
           {
               "C": "CN",
               "L": "Shenzhen",
               "ST": "Shenzhen"
           }
       ]
   }
   
   ```

5. 生成网站证书

   ```shell
   root@master:~/kubernetes/service/https# cfssl gencert -ca=ca.pem -ca-key=ca-key.pem --config=ca-config.json --profile=www service-csr.json | cfssljson -bare server
   2018/10/08 10:50:27 [INFO] generate received request
   2018/10/08 10:50:27 [INFO] received CSR
   2018/10/08 10:50:27 [INFO] generating key: rsa-2048
   2018/10/08 10:50:28 [INFO] encoded CSR
   2018/10/08 10:50:28 [INFO] signed certificate with serial number 74455419700177983253773984610421491449087403369
   2018/10/08 10:50:28 [WARNING] This certificate lacks a "hosts" field. This makes it unsuitable for
   websites. For more information see the Baseline Requirements for the Issuance and Management
   of Publicly-Trusted Certificates, v.1.1.6, from the CA/Browser Forum (https://cabforum.org);
   specifically, section 10.2.3 ("Information Requirements").
   root@master:~/kubernetes/service/https# ls
   ca-config.json  ca.csr  ca-csr.json  ca-key.pem  ca.pem  server.csr  server-key.pem  server.pem  service-csr.json
   
   ```

6. 将证书导入集群管理

   ```shell
   #创建secret
   root@master:~/kubernetes/service/https# kubectl create secret tls jonny-https --key server-key.pem --cert server.pem 
   secret "jonny-https" created
   #查看secret
   root@master:~/kubernetes/service/https# kubectl get secret  
   NAME                  TYPE                                  DATA      AGE
   default-token-hjkdq   kubernetes.io/service-account-token   3         11d
   jonny-https           kubernetes.io/tls                     2         25s
   
   ```


```yaml
Ingress TLS测试：
kubectl create secret tls ingress-secret --key aliangedu-key.pem --cert aliangedu.pem

apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  name: https-test
spec:
  tls:
  - hosts:
    - www.aliangedu.com
    secretName: ingress-secret
  rules:
  - host: www.aliangedu.com
    http:
      paths:
      - backend:
          serviceName: nginx
          servicePort: 88
```

