from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from marshmallow import Schema, fields, ValidationError
from functools import wraps
import os
from dotenv import load_dotenv
import requests
from datetime import datetime
from sqlalchemy import text
import logging

# Configuración inicial
load_dotenv()
app = Flask(__name__)

# Configuración de CORS
CORS(app, resources={
    r"/products": {
        "origins": ["http://localhost:5001", "http://login-service:5001"],
        "methods": ["GET", "OPTIONS"],
        "allow_headers": ["Authorization", "Content-Type"],
        "supports_credentials": True,
        "max_age": 600
    }
})

# Configuración de la base de datos
DB_URI = os.getenv('DB_URI')
if not DB_URI:
    raise ValueError("DB_URI no está configurada en .env")

app.config['SQLALCHEMY_DATABASE_URI'] = DB_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 5,
    'pool_recycle': 300,
    'pool_pre_ping': True
}

# Configuración de logging
logging.basicConfig(level=logging.INFO)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)

db = SQLAlchemy(app)
LOGIN_SERVICE_URL = os.getenv('LOGIN_SERVICE_URL', 'http://login-service:5001')

# Modelos
class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<Product {self.name}>'

# Esquemas
class ProductSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    description = fields.Str()
    price = fields.Float(required=True)  # Cambia de Decimal a Float
    quantity = fields.Int(required=True)

product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

# Helpers
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method == 'OPTIONS':
            return f(*args, **kwargs)
            
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
        
        if not token:
            return jsonify({'message': 'Token faltante'}), 401
        
        try:
            response = requests.get(
                f'{LOGIN_SERVICE_URL}/api/validate-token',
                headers={'Authorization': f'Bearer {token}'},
                timeout=5
            )
            
            if response.status_code != 200:
                return jsonify({'message': 'Token inválido'}), 401
                
            return f(*args, **kwargs)
            
        except requests.exceptions.RequestException as e:
            app.logger.error(f"Error validando token: {str(e)}")
            return jsonify({'message': 'Error validando token'}), 500
            
    return decorated

# Endpoints
@app.route('/products', methods=['GET', 'OPTIONS'])
@token_required
def get_products():
    try:
        db.session.execute(text('SELECT 1')).fetchone()
        products = Product.query.all()
        return jsonify({
            'products': products_schema.dump(products),  # Serialización automática
            'total': len(products)
        })
    except Exception as e:
        app.logger.error(f"Error en /products: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    try:
        db.session.execute(text('SELECT 1')).fetchone()
        return jsonify({
            'status': 'healthy',
            'database': 'connected'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'database': 'disconnected'
        }), 500

# Inicialización
@app.cli.command('init-db')
def init_db():
    """Inicializa la base de datos"""
    with app.app_context():
        db.create_all()
    print("Base de datos inicializada")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)