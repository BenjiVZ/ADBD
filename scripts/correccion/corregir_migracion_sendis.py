import sqlite3

conn = sqlite3.connect('db.sqlite3')
c = conn.cursor()

# Actualizar el nombre de la migración en la base de datos
c.execute('''
    UPDATE django_migrations 
    SET name = '0002_cendis' 
    WHERE app = 'main' AND name = '0002_sendis'
''')

affected = c.rowcount
conn.commit()
conn.close()

print(f"✅ Migración renombrada: {affected} registro(s) actualizado(s)")
print("   '0002_sendis' → '0002_cendis'")
