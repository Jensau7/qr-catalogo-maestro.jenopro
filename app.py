import os
import json
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuración de la base de datos (SQLite por defecto o PostgreSQL si está en Render)
database_url = os.environ.get("DATABASE_URL")
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Carpeta para guardar imágenes de los productos
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Función para cargar la configuración del negocio (nombre, giro, whatsapp y color)
def cargar_config():
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {
            "nombre_negocio": "Catálogo Digital",
            "giro": "Negocio Local",
            "telefono_whatsapp": "6140000000",
            "color_primario": "#d97706"
        }

# Modelo de la base de datos para los productos
class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    imagen = db.Column(db.String(200), nullable=True)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    config = cargar_config()
    productos = Producto.query.all()
    return render_template('panel.html', config=config, productos=productos)

@app.route('/agregar', methods=['POST'])
def agregar():
    nombre = request.form.get('nombre')
    precio = request.form.get('precio')
    descripcion = request.form.get('descripcion')
    imagen_file = request.files.get('imagen')
    
    imagen_path = None
    if imagen_file and imagen_file.filename != '':
        filename = secure_filename(imagen_file.filename)
        imagen_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        imagen_path = f'uploads/{filename}'
        
    try:
        nuevo_prod = Producto(
            nombre=nombre,
            precio=float(precio),
            descripcion=descripcion,
            imagen=imagen_path
        )
        db.session.add(nuevo_prod)
        db.session.commit()
    except Exception as e:
        print(f"Error al guardar: {e}")
        
    return redirect(url_for('index'))

@app.route('/eliminar/<int:id>', methods=['POST'])
def eliminar(id):
    prod = Producto.query.get_or_404(id)
    db.session.delete(prod)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/catalogo')
def catalogo():
    config = cargar_config()
    productos = Producto.query.all()
    return render_template('catalogo.html', config=config, productos=productos)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
