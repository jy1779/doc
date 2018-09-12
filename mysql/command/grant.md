# grant

> 创建用户并授权

创建root用户

```mysql
grant all privileges on *.* to root@'%' identified by '123456';
```

创建mysqldump用户

```mysql
mysql> GRANT USAGE ON xw.* TO 'py_collect'@'%' IDENTIFIED BY 'QkmUuKvk6k1yo';
Query OK, 0 rows affected (0.09 sec)
mysql> GRANT SELECT, INSERT, UPDATE, DELETE ON xw.* TO 'py_collect'@'%';
Query OK, 0 rows affected (0.03 sec)
mysql> grant show view on xw.* to 'py_collect'@'%';
Query OK, 0 rows affected (0.00 sec)
mysql> grant lock tables on xw.* to 'py_collect'@'%';
Query OK, 0 rows affected (0.00 sec)
mysql> grant trigger on xw.* to 'py_collect'@'%';
Query OK, 0 rows affected (0.00 sec)
mysql> grant create on xw.* to 'py_collect'@'%';
Query OK, 0 rows affected (0.03 sec)
```

创建查看slave status用户

```mysql
GRANT REPLICATION CLIENT,SELECT ON xw.* TO 'py_collect'@'%' IDENTIFIED BY 'QkmUuKvk6k1yo';
```

