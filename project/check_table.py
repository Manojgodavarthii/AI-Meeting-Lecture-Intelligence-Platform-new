import mysql.connector
conn = mysql.connector.connect(host='localhost', user='root', password='naga', database='echoaction')
cur = conn.cursor()
cur.execute('SHOW TABLES LIKE "ea_admin_security_settings"')
result = cur.fetchone()
print('Table exists:', result)
if result:
    cur.execute('DESCRIBE ea_admin_security_settings')
    for row in cur.fetchall():
        print(row)
cur.close()
conn.close()