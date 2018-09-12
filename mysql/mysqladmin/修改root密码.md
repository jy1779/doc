# 修改root密码

shell命令行修改密码

mysqladmin -u root password '123'   #没有密码的用户设置密码命令

mysqladmin -u root -p'123' password '456'  #修改管理员密码

mysqladmin -u root -p'MtaF8ZX53KHyiJMj' -h192.168.1.188 -P20002 password ’123456‘

mysqladmin -u root -p'123' password '456' -S /data/3306/mysql.sock #适合多实例方式修改root密码

mysql 命令行修改密码

mysql> update mysql.user set password=password("654") where user='root' and host='localhost'； #设置密码

mysql> flush privileges; #刷新权限

update user set password=password('ksx4bf8uuZDDA') where user='hkm' and host='%';