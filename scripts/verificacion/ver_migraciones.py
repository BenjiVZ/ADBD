import sqlite3

conn = sqlite3.connect('db.sqlite3')
c = conn.cursor()
c.execute('SELECT id, app, name FROM django_migrations WHERE app="main" ORDER BY id')
print("Migraciones aplicadas:")
for row in c.fetchall():
    print(f"{row[0]:3d}. {row[1]}.{row[2]}")
conn.close()
