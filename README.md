初始设置：

## 创建数据库：
* 参考[「设置mysql utf-8」](http://stackoverflow.com/questions/3513773/change-mysql-default-character-set-to-utf-8-in-my-cnf)
设置mysql的编码
* 连接数据库输入以下命令建立数据库
```sql
drop database thu_learn;
create database thu_learn;
use thu_learn;
create table CourseName (CID int primary key, Name varchar(30), UID int, UPd blob);
create table Work (WID int primary key, CID int, EndTime date, Text TEXT, Title varchar(63));
create table Message (MID int primary key, CID int, Time date, Text TEXT, Title varchar(63));
create table UserInfo (UID int primary key, UPd blob, OpenID varchar(30));
create table UserCourse (UID int, CID int, primary key(UID, CID));
create table WorkFinished (UID int, WID int, primary key(UID, WID));
show variables like '%character%';
show tables;
```
* 禁用数据库缓存
mysql的缓存机制问题：pymysql会从缓存中返回数据，而一个connection作出的改动，并不能导致另一个connection更新缓存。
可能的两种解决方案：限定每个数据库只能一个connection访问，或者禁止使用缓存。
找到/etc/mysql/my.cnf，然后查找并修改

```
query_cache_limit	= 0
query_cache_size    = 0
```
然后重启mysql服务。【简单粗暴的方法：重启系统】
在mysql客户端执行```show variables like '%cache%';```查看缓存情况


## 进入测试号/公众号设置下列三个模板消息：
1.
模板标题：```新发布的作业```
模板内容：
```
{{coursename.DATA}}
{{title.DATA}}
截止时间：{{endtime.DATA}}
{{text.DATA}}
```
2.
模板标题：```新发布的公告```
模板内容：
```
{{coursename.DATA}}
{{title.DATA}}
发布时间：{{time.DATA}}
{{text.DATA}}
```
3.
模板标题：```信息导入成功```
模板内容：
```
恭喜{{studentnumber.DATA}}同学，你的快速查询服务已全部开启。
```


## 设置系统参数
修改secret.example.json，填入相应内容
将其改名为 ".secret.json"放入src目录下


