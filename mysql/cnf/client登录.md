# client登录

```shell
cat .master.cnf
[client]
host = 127.0.0.1
user = root
password =passwd

#登录
mysql --defaults-extra-file=/root/scripts/mysql/.master.cnf
```

