from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import datetime
import random
import os

app = Flask(__name__)
CORS(app)
DB_NAME = 'master_ley.db'

# Inicializar la base de datos al arrancar
init_db()
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            usuario_id TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            tipo_cuenta TEXT DEFAULT 'GRATIS',
            retos_respondidos_hoy INTEGER DEFAULT 0,
            ultimo_acceso TEXT,
            tema_actual INTEGER DEFAULT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS articulos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero INTEGER UNIQUE,
            titulo TEXT,
            contenido TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS preguntas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            articulo_id INTEGER NOT NULL,
            enunciado TEXT NOT NULL,
            opcion_a TEXT NOT NULL,
            opcion_b TEXT NOT NULL,
            opcion_c TEXT NOT NULL,
            opcion_d TEXT NOT NULL,
            respuesta_correcta TEXT NOT NULL,
            explicacion TEXT,
            FOREIGN KEY (articulo_id) REFERENCES articulos(id)
        )
    ''')
    conn.commit()

    # Insertar artículos por defecto
    articulos_data = [
        (334, 'Control Difuso y Concentrado', 'Artículo 334...'),
        (335, 'TSJ como máximo intérprete', 'Artículo 335...'),
        (340, 'Enmienda Constitucional', 'La enmienda tiene por objeto...')
    ]
    for num, tit, cont in articulos_data:
        cursor.execute("INSERT OR IGNORE INTO articulos (numero, titulo, contenido) VALUES (?,?,?)", (num, tit, cont))
    conn.commit()

    # Insertar preguntas de ejemplo si está vacío
    cursor.execute("SELECT COUNT(*) FROM preguntas")
    if cursor.fetchone()[0] == 0:
        preguntas = [
            (1, 'Un juez de municipio desaplica una ordenanza por inconstitucional. ¿Qué control ejerce?', 
             'Control concentrado', 'Control difuso', 'Control de legalidad', 'Control de convencionalidad', 'B', 
             'El control difuso permite a cualquier juez desaplicar una norma en un caso concreto, sin anularla.'),
            (1, '¿Quién declara la nulidad de una ley nacional con efectos generales?',
             'Cualquier juez', 'La Sala Constitucional del TSJ', 'El Presidente', 'La Asamblea Nacional', 'B',
             'Solo la Sala Constitucional ejerce el control concentrado con efectos erga omnes.'),
            (2, 'Las interpretaciones de la Sala Constitucional son vinculantes para:',
             'Solo para el caso resuelto', 'Para todas las salas del TSJ y demás tribunales', 'Solo para tribunales penales', 'Ninguna es correcta', 'B',
             'Según el Art. 335, las interpretaciones de la Sala Constitucional son vinculantes para todas las salas del TSJ y para todos los tribunales.'),
            (2, '¿Quién es el máximo y último intérprete de la Constitución?',
             'El Presidente', 'La Asamblea Nacional', 'La Sala Constitucional del TSJ', 'El Fiscal General', 'C',
             'La Sala Constitucional es el máximo intérprete según el Art. 335.')
        ]
        cursor.executemany(
            "INSERT INTO preguntas (articulo_id, enunciado, opcion_a, opcion_b, opcion_c, opcion_d, respuesta_correcta, explicacion) VALUES (?,?,?,?,?,?,?,?)",
            preguntas
        )
        conn.commit()
    conn.close()

# Rutas de la API
@app.route('/api/articulos', methods=['GET'])
def get_articulos():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, numero, titulo FROM articulos")
    articulos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(articulos)

@app.route('/api/usuario/<usuario_id>', methods=['GET'])
def get_usuario(usuario_id):
    conn = get_db()
    cursor = conn.cursor()
    fecha_hoy = datetime.date.today().isoformat()
    cursor.execute("SELECT * FROM usuarios WHERE usuario_id = ?", (usuario_id,))
    usuario = cursor.fetchone()
    if not usuario:
        cursor.execute("INSERT INTO usuarios (usuario_id, nombre, tipo_cuenta, retos_respondidos_hoy, ultimo_acceso) VALUES (?, 'Estudiante', 'GRATIS', 0, ?)", (usuario_id, fecha_hoy))
        conn.commit()
        cursor.execute("SELECT * FROM usuarios WHERE usuario_id = ?", (usuario_id,))
        usuario = cursor.fetchone()
    else:
        if usuario['ultimo_acceso'] != fecha_hoy:
            cursor.execute("UPDATE usuarios SET retos_respondidos_hoy = 0, ultimo_acceso = ? WHERE usuario_id = ?", (fecha_hoy, usuario_id))
            conn.commit()
            cursor.execute("SELECT * FROM usuarios WHERE usuario_id = ?", (usuario_id,))
            usuario = cursor.fetchone()
    conn.close()
    return jsonify(dict(usuario))

@app.route('/api/usuario/<usuario_id>/tema/<int:articulo_id>', methods=['POST'])
def set_tema(usuario_id, articulo_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET tema_actual = ? WHERE usuario_id = ?", (articulo_id, usuario_id))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@app.route('/api/pregunta/<usuario_id>', methods=['GET'])
def get_pregunta(usuario_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT tema_actual, tipo_cuenta, retos_respondidos_hoy FROM usuarios WHERE usuario_id = ?", (usuario_id,))
    usuario = cursor.fetchone()
    if not usuario or not usuario['tema_actual']:
        conn.close()
        return jsonify({"error": "No hay tema seleccionado"}), 400
    if usuario['tipo_cuenta'] == 'GRATIS' and usuario['retos_respondidos_hoy'] >= 3:
        conn.close()
        return jsonify({"error": "Límite de retos gratuitos alcanzado"}), 429

    cursor.execute("SELECT * FROM preguntas WHERE articulo_id = ? ORDER BY RANDOM() LIMIT 1", (usuario['tema_actual'],))
    pregunta = cursor.fetchone()
    conn.close()
    if not pregunta:
        return jsonify({"error": "No hay preguntas para este tema"}), 404
    return jsonify(dict(pregunta))

@app.route('/api/responder/<usuario_id>', methods=['POST'])
def responder(usuario_id):
    data = request.json
    pregunta_id = data['pregunta_id']
    respuesta = data['respuesta']
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT respuesta_correcta, explicacion FROM preguntas WHERE id = ?", (pregunta_id,))
    pregunta = cursor.fetchone()
    
    correcta = (respuesta == pregunta['respuesta_correcta'])
    
    cursor.execute("SELECT tipo_cuenta FROM usuarios WHERE usuario_id = ?", (usuario_id,))
    usuario = cursor.fetchone()
    if usuario and usuario['tipo_cuenta'] == 'GRATIS':
        cursor.execute("UPDATE usuarios SET retos_respondidos_hoy = retos_respondidos_hoy + 1 WHERE usuario_id = ?", (usuario_id,))
        conn.commit()
    conn.close()
    
    return jsonify({
        "correcta": correcta,
        "respuesta_correcta": pregunta['respuesta_correcta'],
        "explicacion": pregunta['explicacion']
    })

# Ruta para servir el frontend
@app.route('/')
@app.route('/index.html')
def serve_frontend():
    return send_from_directory('.', 'index.html')

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
