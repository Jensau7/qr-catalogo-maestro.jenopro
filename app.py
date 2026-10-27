import os
import json
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__)

database_url = os.environ.get("DATABASE_URL")
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

BASE_UPLOAD_FOLDER = 'static/uploads'
app.config['BASE_UPLOAD_FOLDER'] = BASE_UPLOAD_FOLDER

def cargar_config():
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error leyendo config.json: {e}")
        return {
            "nombre_negocio": "Catálogo Digital",
            "giro": "Negocio Local",
            "telefono_whatsapp": "6140000000",
            "color_primario": "#d97706"
        }

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
    try:
        config = cargar_config()
        nombre_negocio = config.get("nombre_negocio", "default")
        nombre_carpeta = ''.join(c if c.isalnum() else '_' for c in nombre_negocio.lower())
        
        upload_folder = os.path.join(app.root_path, 'static', 'uploads', nombre_carpeta)
        os.makedirs(upload_folder, exist_ok=True)

        nombre = request.form.get('nombre')
        precio = request.form.get('precio')
        descripcion = request.form.get('descripcion')
        imagen_file = request.files.get('imagen')
        
        imagen_path = None
        if imagen_file and imagen_file.filename != '':
            filename = secure_filename(imagen_file.filename)
            file_path = os.path.join(upload_folder, filename)
            imagen_file.save(file_path)
            imagen_path = f'uploads/{nombre_carpeta}/{filename}'
            
        nuevo_prod = Producto(
            nombre=nombre,
            precio=float(precio) if precio else 0.0,
            descripcion=descripcion,
            imagen=imagen_path
        )
        db.session.add(nuevo_prod)
        db.session.commit()
    except Exception as e:
        print(f"ERROR CRÍTICO AL AGREGAR: {e}")
        
    return redirect(url_for('index'))

@app.route('/eliminar/<int:id>', methods=['POST'])
def eliminar(id):
    prod = Producto.query.get_or_404(id)
    if prod.imagen:
        try:
            ruta_fisica = os.path.join(app.root_path, 'static', prod.imagen)
            if os.path.exists(ruta_fisica):
                os.remove(ruta_fisica)
        except Exception as e:
            print(f"Error borrando archivo: {e}")
            
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
