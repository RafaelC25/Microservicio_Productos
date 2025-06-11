# app.py
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from marshmallow import Schema, fields, ValidationError
from dotenv import load_dotenv
import os
from datetime import datetime

# Cargar variables de entorno desde .env
if os.path.exists('.env'):
    load_dotenv()

# =============================================
# Configuración de la aplicación Flask
# =============================================
app = Flask(__name__)
CORS(app)  # Habilitar CORS

# Configuración de PostgreSQL con Neon.tech (desde variable de entorno)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_URI')  # Ejemplo: postgresql+psycopg2://user:pass@ep-example.us-east-2.aws.neon.tech/db?sslmode=require

# Configuración adicional para producción
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 5,          # Tamaño del pool de conexiones
    'pool_recycle': 300,     # Reciclar conexiones cada 300 segundos (Neon cierra conexiones inactivas a los 5 minutos)
    'pool_pre_ping': True    # Verificar conexiones antes de usarlas
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# Modelo de Producto

class Product(db.Model):
    __tablename__ = 'products'  # Nombre explícito de la tabla
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)  # Usamos Text en lugar de String para mayor capacidad
    price = db.Column(db.Numeric(10, 2), nullable=False)  # Tipo NUMERIC para precisión decimal
    quantity = db.Column(db.Integer, nullable=False)
   
    def __repr__(self):
        return f'<Product {self.name}>'
    
class Sale(db.Model):
    __tablename__ = 'sale'  # Nombre de la tabla en la BD
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)  # Relación con Product
    quantity = db.Column(db.Integer, nullable=False)  # Cantidad vendida
    sale_date = db.Column(db.DateTime, server_default=db.text('CURRENT_TIMESTAMP'))  # Fecha automática
    total_venta = db.Column(db.Numeric(10, 2), nullable=False)  # Total de la venta
    

# =============================================
# Esquema de Validación
# =============================================
class ProductSchema(Schema):
    id = fields.Int(dump_only=True)  # Solo para respuesta, no para validación
    name = fields.Str(required=True, error_messages={"required": "El nombre es obligatorio"})
    description = fields.Str()
    price = fields.Decimal(required=True, places=2, error_messages={"required": "El precio es obligatorio"})
    quantity = fields.Int(required=True, error_messages={"required": "La cantidad es obligatoria"})
    
class SaleSchema(Schema):
    id = fields.Int(dump_only=True)
    product_id = fields.Int(required=True)
    quantity = fields.Int(required=True)
    sale_date = fields.DateTime(format='%Y-%m-%d %H:%M:%S', dump_only=True)
    total_venta = fields.Decimal(required=True, places=2, dump_only=True)

product_schema = ProductSchema()
products_schema = ProductSchema(many=True)
sale_schema = SaleSchema()
sales_schema = SaleSchema(many=True)

# =============================================
# Endpoints CRUD
# =============================================
@app.route('/products', methods=['GET'])
def get_products():
    """Obtener todos los productos con paginación básica"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        products = Product.query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'products': products_schema.dump(products.items),
            'total': products.total,
            'pages': products.pages,
            'current_page': products.page
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    """Obtener un producto por ID"""
    try:
        product = Product.query.get_or_404(id)
        return jsonify(product_schema.dump(product))
    except Exception as e:
        return jsonify({"error": str(e)}), 404 if '404' in str(e) else 500

@app.route('/products', methods=['POST'])
def create_product():
    """Crear un nuevo producto con validación"""
    try:
        data = request.get_json()
        errors = product_schema.validate(data)
        if errors:
            return jsonify(errors), 400
            
        new_product = Product(
            name=data['name'],
            description=data.get('description'),
            price=data['price'],
            quantity=data['quantity']
        )
        
        db.session.add(new_product)
        db.session.commit()
        
        return jsonify(product_schema.dump(new_product)), 201
    except ValidationError as e:
        return jsonify(e.messages), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    """Actualizar producto existente"""
    try:
        product = Product.query.get_or_404(id)
        data = request.get_json()
        
        # Validación parcial (solo campos proporcionados)
        if 'name' in data:
            product.name = data['name']
        if 'description' in data:
            product.description = data['description']
        if 'price' in data:
            product.price = data['price']
        if 'quantity' in data:
            product.quantity = data['quantity']
        
        db.session.commit()
        return jsonify(product_schema.dump(product))
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    """Eliminar producto"""
    try:
        product = Product.query.get_or_404(id)
        db.session.delete(product)
        db.session.commit()
        return jsonify({"message": "Producto eliminado correctamente"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    

@app.route('/products/sell/<int:id>', methods=['POST'])
def sell_product(id):
    try:
        data = request.get_json()
        quantity_sold = data.get('quantity', 1)
        # Validación de cantidad vendida
        if quantity_sold <= 0:
            return jsonify({"error": "La cantidad vendida debe ser mayor que cero"}), 400
        product = Product.query.get_or_404(id)
        
        if product.quantity < quantity_sold:
            return jsonify({"error": "Stock insuficiente"}), 400
        
        # Iniciar transacción
        product.quantity -= quantity_sold
        total_venta = product.price * quantity_sold
        
        # Registrar la venta
        new_sale = Sale(
            product_id=id,
            quantity=quantity_sold,
            sale_date=datetime.now(),  # Fecha y hora actual
            total_venta=total_venta
        )
        db.session.add(new_sale)
        db.session.commit()
        
        return jsonify({
            "message": "Venta registrada exitosamente",
            "sale": {
                "id": new_sale.id,
                "product_id": new_sale.product_id,
                "product_name": product.name,
                "quantity": new_sale.quantity,
                "sale_date": new_sale.sale_date.isoformat(),
                "total_venta": str(new_sale.total_venta)  # Convertir a string para JSON
            },
            "remaining_stock": product.quantity
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/sales', methods=['GET'])
def get_sales():
    """Obtener todas las ventas con paginación"""
    try:
        # Paginación (opcional)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        sales = Sale.query.order_by(Sale.sale_date.desc()).paginate(
            page=page, 
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            "sales": sales_schema.dump(sales.items),
            "total": sales.total,
            "pages": sales.pages,
            "current_page": sales.page
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =============================================
# Inicialización de la Base de Datos
# =============================================
@app.cli.command('init-db')
def init_db():
    """Comando para crear tablas (ejecutar manualmente)"""
    with app.app_context():
        db.create_all()
    print("Tablas creadas correctamente")

# =============================================
# Punto de Entrada
# =============================================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

