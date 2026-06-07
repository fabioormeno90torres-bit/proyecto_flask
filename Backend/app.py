import os
import sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS

# Inicialización limpia de la API (Sin carpetas de templates)
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'mi_clave_secreta_super_segura_unfv')

# ¡CRUCIAL! CORS permite que tu dominio de Vercel se conecte a Render sin bloqueos
CORS(app, supports_credentials=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'database.db')

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row 
    return conn

def inicializar_base_datos_auto():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            nombre TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            precio REAL NOT NULL,
            stock INTEGER NOT NULL,
            categoria TEXT
        )
    ''')
    
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO usuarios (username, password, nombre) VALUES (?, ?, ?)", 
                       ('admin', '1234', 'Fabio Ormeño'))
    
    cursor.execute("SELECT COUNT(*) FROM productos")
    if cursor.fetchone()[0] == 0:
        productos_prueba = [
            ('P001', 'Laptop ASUS ROG', 'Laptop Gamer AMD Ryzen 7, 16GB RAM, 512GB SSD', 4500.0, 10, 'Tecnología'),
            ('P002', 'Mouse Logi Master 3S', 'Mouse inalámbrico ergonómico avanzado para desarrolladores', 420.0, 25, 'Accesorios'),
            ('P003', 'Teclado Mecánico Keychron Q1', 'Teclado mecánico custom 75% con switches Gateron Pro', 750.0, 5, 'Accesorios'),
            ('P004', 'Monitor Dell UltraSharp 27"', 'Monitor 4K ideal para diseño y visualización de código', 1850.0, 8, 'Tecnología')
        ]
        cursor.executemany(
            "INSERT INTO productos (codigo, nombre, descripcion, precio, stock, categoria) VALUES (?, ?, ?, ?, ?, ?)", 
            productos_prueba
        )
            
    conn.commit()
    conn.close()

# --- ENRUTAMIENTO API REST (JSON) ---

# API LOGIN
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'Datos no proporcionados'}), 400
        
    username = data.get('username')
    password = data.get('password')
    
    conn = get_db_connection()
    usuario = conn.execute('SELECT * FROM usuarios WHERE username = ? AND password = ?',
                           (username, password)).fetchone()
    conn.close()
    
    if usuario:
        # Devolvemos los datos del usuario para que el Frontend los guarde en su memoria (localStorage)
        return jsonify({
            'status': 'success',
            'message': 'Autenticación exitosa',
            'data': {
                'username': usuario['username'],
                'nombre': usuario['nombre']
            }
        }), 200
    else:
        return jsonify({'status': 'error', 'message': 'Usuario o contraseña incorrectos'}), 401

# API BUSCADOR
@app.route('/api/buscar_producto', methods=['POST'])
def buscar_producto():
    data = request.get_json() if request.is_json else request.form
    codigo = data.get('codigo', '').strip()
    
    if not codigo:
        return jsonify({'status': 'error', 'message': 'Código no proporcionado'}), 400
        
    conn = get_db_connection()
    producto = conn.execute('SELECT * FROM productos WHERE codigo = ?', (codigo,)).fetchone()
    conn.close()
    
    if producto:
        return jsonify({
            'status': 'success',
            'data': {
                'codigo': producto['codigo'],
                'nombre': producto['nombre'],
                'descripcion': producto['descripcion'],
                'precio': producto['precio'],
                'stock': producto['stock'],
                'categoria': producto['categoria']
            }
        }), 200
    else:
        return jsonify({'status': 'error', 'message': 'Producto no encontrado'}), 404

# Inicialización e inicio
inicializar_base_datos_auto()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)