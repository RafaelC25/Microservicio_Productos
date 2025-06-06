from flask import Flask, render_template, request, redirect, url_for, session, make_response, jsonify
from functools import wraps
from auth import generate_token, validate_token
from models import verify_user
import os
from dotenv import load_dotenv
from datetime import timedelta

# Configuración inicial
load_dotenv()
app = Flask(__name__)

# Configuración de sesión segura
app.secret_key = os.getenv('SECRET_KEY', 'clave-secreta-desarrollo')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False  # True en producción con HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)

PRODUCT_SERVICE_URL = os.getenv('PRODUCT_SERVICE_URL', 'http://product-service:5000')

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Si ya está autenticado, redirigir al dashboard
    if 'user' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            return render_template('login.html', error="Usuario y contraseña requeridos"), 400
        
        if verify_user(username, password):
            token = generate_token(username)
            session.permanent = True
            session['user'] = username
            session['token'] = token
            
            response = make_response(redirect(url_for('dashboard')))
            response.set_cookie(
                'token',
                token,
                httponly=True,
                secure=False,  # True en producción
                samesite='Lax',
                max_age=3600  # 1 hora de expiración
            )
            return response
        
        return render_template('login.html', error="Credenciales inválidas"), 401
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    # Verificar autenticación por sesión o cookie
    token = session.get('token') or request.cookies.get('token')
    
    if not token:
        return redirect(url_for('login'))
    
    try:
        # Validar el token JWT
        payload = validate_token(token)
        return render_template('dashboard.html', username=payload['user'])
    except Exception as e:
        print(f"Error validando token: {str(e)}")
        return redirect(url_for('login'))
    
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        # Mostrar formulario de registro (HTML)
        return render_template('register.html')
    
    elif request.method == 'POST':
        # Procesar registro
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 415
        
        data = request.get_json()
        
        # Validar datos requeridos
        required_fields = ['username', 'password', 'email']
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400
        
        # Validar longitud mínima de contraseña
        if len(data['password']) < 8:
            return jsonify({"error": "Password must be at least 8 characters"}), 400
        
        # Aquí iría la lógica para verificar si el usuario ya existe en tu DB
        # user_exists = User.query.filter_by(username=data['username']).first()
        # if user_exists:
        #     return jsonify({"error": "Username already taken"}), 409
        
        # Crear nuevo usuario (ejemplo)
        try:
            # hashed_password = generate_password_hash(data['password'])
            # new_user = User(
            #     username=data['username'],
            #     email=data['email'],
            #     password=hashed_password
            # )
            # db.session.add(new_user)
            # db.session.commit()
            
            # Respuesta exitosa
            return jsonify({
                "message": "User registered successfully",
                "redirect": "/login",
                "user": {
                    "username": data['username'],
                    "email": data['email']
                }
            }), 201
        
        except Exception as e:
            # db.session.rollback()
            return jsonify({"error": str(e)}), 500

@app.route('/logout')
def logout():
    # Limpiar sesión y cookies
    session.clear()
    response = make_response(redirect(url_for('login')))
    response.delete_cookie('token')
    return response

@app.route('/api/validate-token', methods=['GET'])
def api_validate_token():
    """Endpoint para que product-service valide tokens"""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({"valid": False, "error": "Formato de token inválido"}), 401
    
    token = auth_header.split(' ')[1]
    try:
        payload = validate_token(token)
        return jsonify({
            "valid": True,
            "user": payload['user'],
            "token": token
        }), 200
    except Exception as e:
        return jsonify({"valid": False, "error": str(e)}), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)