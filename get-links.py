#!/usr/bin/python3
import getpass
import os
import sys

import MySQLdb

key = sys.argv[1] if len(sys.argv)==2 else None

if not key:
    sys.exit('''
Ha de pasar un nombre de fichero para el resultado (preferentemente la ip del dominio)
Solo el nombre, no añada ni la extenisión ni la ruta.
    '''.strip())

if 'MYSQL_USER_READ' in os.environ:
    user, passwd = os.environ['MYSQL_USER_READ'].split()
else:
    user = input("Username: ")
    passwd = getpass.getpass("Password: ")


def execute(cursor, file):
    _sql = None
    with open(file, 'r') as myfile:
        _sql = myfile.read()
    cursor.execute(_sql)
    return cursor.fetchall()


db = MySQLdb.connect("localhost", user, passwd)

cursor = db.cursor()

results = execute(cursor, 'search-wp.sql')

sql = "select distinct guid from ("

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
out = "data/%s.txt" % (key)
with open(out, "w") as f:
    for row in results:
        f.write(row[0]+"\n")

db.close()

print("Resultado guardado en %s" % out)
