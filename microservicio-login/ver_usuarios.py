import sqlite3

conn = sqlite3.connect('users.db')
cursor = conn.cursor()

cursor.execute("SELECT id, username, nombre, apellidos, celular, email, direccion FROM users")
usuarios = cursor.fetchall()

for usuario in usuarios:
    print(usuario)

conn.close()
