import mysql.connector
conn = mysql.connector.connect(host='localhost', user='root', password='naga', database='echoaction')
cur = conn.cursor()
cur.execute('SELECT email, password FROM ea_registration WHERE email IN ("test@test.com", "godaverthinagamanojbalaji@gmail.com")')
for row in cur.fetchall():
    print(f'Email: {row[0]}, Password hash: {row[1][:50]}...')
cur.close()
conn.close()