import os
import json
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

database_url = os.environ.get("DATABASE_URL")
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

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
    imagen = db.Column(db.Text, nullable=True)

with app.app_context():
    try:
        # Si la base vieja da problemas de columnas, la reiniciamos limpia de forma segura
        db.create_all()
    except Exception as e:
        print(f"Aviso de BD: {e}")

@app.route('/')
def index():
    try:
        config = cargar_config()
        productos = Producto.query.all()
        return render_template('panel.html', config=config, productos=productos)
    except Exception as e:
        # Si hay error en la tabla vieja, la borramos y la recreamos limpia al vuelo
        try:
            db.drop_all()
            db.create_all()
            config = cargar_config()
            productos = Producto.query.all()
            return render_template('panel.html', config=config, productos=productos)
        except Exception as ex:
            return f"Error crítico recuperando base de datos: {ex}", 500

@app.route('/agregar', methods=['POST'])
def agregar():
    try:
        nombre = request.form.get('nombre')
        precio = request.form.get('precio')
        descripcion = request.form.get('descripcion')
        imagen_url = request.form.get('imagen')
        
        nuevo_prod = Producto(
            nombre=nombre,
            precio=float(precio) if precio else 0.0,
            descripcion=descripcion,
            imagen=imagen_url
        )
        db.session.add(nuevo_prod)
        db.session.commit()
    except Exception as e:
        print(f"ERROR AL AGREGAR: {e}")
        
    return redirect(url_for('index'))

@app.route('/eliminar/<int:id>', methods=['POST'])
def eliminar(id):
    try:
        prod = Producto.query.get_or_404(id)
        db.session.delete(prod)
        db.session.commit()
    except Exception as e:
        print(f"ERROR AL ELIMINAR: {e}")
    return redirect(url_for('index'))

@app.route('/catalogo')
def catalogo():
    try:
        config = cargar_config()
        productos = Producto.query.all()
        return render_template('catalogo.html', config=config, productos=productos)
    except Exception as e:
        return f"Error en catálogo: {e}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
