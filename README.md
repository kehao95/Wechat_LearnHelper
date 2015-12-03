create database and tables

http://stackoverflow.com/questions/3513773/change-mysql-default-character-set-to-utf-8-in-my-cnf


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

