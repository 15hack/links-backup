#!/usr/bin/python3
from subprocess import Popen, PIPE
import getpass
import MySQLdb
import sys
import os

if 'MYSQL_USER_READ' in os.environ:
	user, passwd = os.environ['MYSQL_USER_READ'].split()
else:
	user = input("Username: ")
	passwd = getpass.getpass("Password: ")

def execute(cursor, file):
	_sql=None
	with open(file, 'r') as myfile:
		_sql=myfile.read()
	cursor.execute(_sql)
	return cursor.fetchall()

db = MySQLdb.connect("localhost", user, passwd)

cursor = db.cursor()

results = execute(cursor, 'search-wp.sql')

sql="select distinct guid from ("

for row in results:
	sql = sql+'''
	(
		select guid
		from %s.%s
		where
		post_status = 'publish' and
		post_type in ('post', 'page')
	)
	UNION
	'''.rstrip() % row

sql = sql[:-7]

sql = sql + "\n) T order by guid"

cursor.execute(sql)

results = cursor.fetchall()
with open("data/links.txt", "w") as f:
	for row in results:
		f.write(row[0]+"\n")

db.close()
