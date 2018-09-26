# 自签TLS证书

| 组件           | 证书                                     |
| -------------- | ---------------------------------------- |
| etcd           | ca.pem,server.pem,server-key.pem         |
| kube-apiserver | ca.pem,server.pem,server-key.pem         |
| kubelet        | ca.pem,ca-key.pem                        |
| kube-proxy     | ca.pem,kube-proxy.pem,kube-proxy-key.pem |
| kubectl        | ca.pem,admin.pem,admin-key.pem           |
| flannel        | ca.pem,server.pem,server-key.pem         |

安装证书生成工具cfssl：
wget https://pkg.cfssl.org/R1.2/cfssl_linux-amd64
wget https://pkg.cfssl.org/R1.2/cfssljson_linux-amd64
wget https://pkg.cfssl.org/R1.2/cfssl-certinfo_linux-amd64
chmod +x cfssl_linux-amd64 cfssljson_linux-amd64 cfssl-certinfo_linux-amd64
mv cfssl_linux-amd64 /usr/local/bin/cfssl
mv cfssljson_linux-amd64 /usr/local/bin/cfssljson
mv cfssl-certinfo_linux-amd64 /usr/bin/cfssl-certinfo

生成证书的模板文件

```shell
root@k8s-master:~/ssl# cfssl print-defaults config
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

颁发证书文件模板

```shell
root@k8s-master:~/ssl# cfssl print-defaults csr
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

```

生产ca.pem，ca-key.pem

```shell
cat > ca-config.json <<EOF
{
  "signing": {
    "default": {
      "expiry": "87600h"
    },
    "profiles": {
      "kubernetes": {
         "expiry": "87600h",
         "usages": [
            "signing",
            "key encipherment",
            "server auth",
            "client auth"
        ]
      }
    }
  }
}
EOF

cat > ca-csr.json <<EOF
{
    "CN": "kubernetes",
    "key": {
        "algo": "rsa",
        "size": 2048
    },
    "names": [
        {
            "C": "CN",
            "L": "Shenzhen",
            "ST": "Shenzhen",
      	    "O": "k8s",
            "OU": "System"
        }
    ]
}
EOF
root@k8s-master:~/ssl# cfssl gencert -initca ca-csr.json | cfssljson -bare ca -
2018/09/18 10:38:54 [INFO] generating a new CA key and certificate from CSR
2018/09/18 10:38:54 [INFO] generate received request
2018/09/18 10:38:54 [INFO] received CSR
2018/09/18 10:38:54 [INFO] generating key: rsa-2048
2018/09/18 10:38:55 [INFO] encoded CSR
2018/09/18 10:38:55 [INFO] signed certificate with serial number 169678645679135433800540957517814616559867885843
root@k8s-master:~/ssl# ls *.pem
ca-key.pem  ca.pem

```

生成server证书，用于api和etcd的http请求

```shell
cat > server-csr.json <<EOF
{
    "CN": "kubernetes",
    "hosts": [
      "127.0.0.1",
      "192.168.1.67",
      "192.168.1.69",
      "10.10.10.1",
      "kubernetes",
      "kubernetes.default",
      "kubernetes.default.svc",
      "kubernetes.default.svc.cluster",
      "kubernetes.default.svc.cluster.local"
    ],
    "key": {
        "algo": "rsa",
        "size": 2048
    },
    "names": [
        {
            "C": "CN",
            "L": "Shenzhen",
            "ST": "Shenzhen",
            "O": "k8s",
            "OU": "System"
        }
    ]
}
EOF
root@k8s-master:~/ssl# cfssl gencert -ca=ca.pem -ca-key=ca-key.pem -config=ca-config.json -profile=kubernetes server-csr.json | cfssljson -bare server
2018/09/18 10:51:20 [INFO] generate received request
2018/09/18 10:51:20 [INFO] received CSR
2018/09/18 10:51:20 [INFO] generating key: rsa-2048
2018/09/18 10:51:20 [INFO] encoded CSR
2018/09/18 10:51:20 [INFO] signed certificate with serial number 323081214970870529285823089900195640366876988565
2018/09/18 10:51:20 [WARNING] This certificate lacks a "hosts" field. This makes it unsuitable for
websites. For more information see the Baseline Requirements for the Issuance and Management
of Publicly-Trusted Certificates, v.1.1.6, from the CA/Browser Forum (https://cabforum.org);
specifically, section 10.2.3 ("Information Requirements").
root@k8s-master:~/ssl# ls server*
server.csr  server-csr.json  server-key.pem  server.pem

```

生成admin证书集群管理员使用

```shell
cat > admin-csr.json <<EOF
{
  "CN": "admin",
  "hosts": [],
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names": [
    {
      "C": "CN",
      "L": "Shenzhen",
      "ST": "Shenzhen",
      "O": "system:masters",
      "OU": "System"
    }
  ]
}
EOF
root@k8s-master:~/ssl# cfssl gencert -ca=ca.pem -ca-key=ca-key.pem -config=ca-config.json -profile=kubernetes admin-csr.json | cfssljson -bare admin
2018/09/18 10:57:00 [INFO] generate received request
2018/09/18 10:57:00 [INFO] received CSR
2018/09/18 10:57:00 [INFO] generating key: rsa-2048
2018/09/18 10:57:00 [INFO] encoded CSR
2018/09/18 10:57:00 [INFO] signed certificate with serial number 723833734617212005307266608325387636508170977393
2018/09/18 10:57:00 [WARNING] This certificate lacks a "hosts" field. This makes it unsuitable for
websites. For more information see the Baseline Requirements for the Issuance and Management
of Publicly-Trusted Certificates, v.1.1.6, from the CA/Browser Forum (https://cabforum.org);
specifically, section 10.2.3 ("Information Requirements").
root@k8s-master:~/ssl# ls admin*
admin.csr  admin-csr.json  admin-key.pem  admin.pem

```

生成kube-proxy证书

```shell
cat > kube-proxy-csr.json <<EOF
{
  "CN": "system:kube-proxy",
  "hosts": [],
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names": [
    {
      "C": "CN",
      "L": "Shenzhen",
      "ST": "Shenzhen",
      "O": "k8s",
      "OU": "System"
    }
  ]
}
EOF
root@k8s-master:~/ssl# cfssl gencert -ca=ca.pem -ca-key=ca-key.pem -config=ca-config.json -profile=kubernetes kube-proxy-csr.json | cfssljson -bare kube-proxy
2018/09/18 11:28:33 [INFO] generate received request
2018/09/18 11:28:33 [INFO] received CSR
2018/09/18 11:28:33 [INFO] generating key: rsa-2048
2018/09/18 11:28:34 [INFO] encoded CSR
2018/09/18 11:28:34 [INFO] signed certificate with serial number 186623992015237658595614266197758510945412511502
2018/09/18 11:28:34 [WARNING] This certificate lacks a "hosts" field. This makes it unsuitable for
websites. For more information see the Baseline Requirements for the Issuance and Management
of Publicly-Trusted Certificates, v.1.1.6, from the CA/Browser Forum (https://cabforum.org);
specifically, section 10.2.3 ("Information Requirements").

```

所用到的证书

```shell
root@k8s-master:~/ssl# ls
admin-key.pem  admin.pem  ca-key.pem  ca.pem  kube-proxy-key.pem  kube-proxy.pem  server-key.pem  server.pem
```

