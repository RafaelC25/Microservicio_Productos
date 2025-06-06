import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            nombre TEXT,
            apellidos TEXT,
            celular TEXT,
            email TEXT UNIQUE,
            direccion TEXT
        )
    ''')
    conn.commit()
    conn.close()

def verify_user(username, password):
    conn = None
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT password FROM users 
            WHERE username = ? COLLATE NOCASE
            LIMIT 1
        """, (username,))
        
        row = cursor.fetchone()
        
        if not row:
            print(f"Usuario no encontrado: {username}")
            return False
            
        stored_hash = row[0]
        if not stored_hash:
            print(f"Hash vacío para usuario: {username}")
            return False
            
        return check_password_hash(stored_hash, password)
        
    except sqlite3.Error as e:
        print(f"Error de base de datos: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()