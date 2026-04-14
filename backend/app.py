from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import pandas as pd
from datetime import datetime

app = Flask(__name__)
CORS(app)

DB_NAME = "bienes.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Tabla principal de bienes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bienes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_patrimonial TEXT NOT NULL UNIQUE,
            nombre TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL,
            persona_asignada TEXT NOT NULL
        )
    """)

    # Tabla de historial de movimientos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historial (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bien_id INTEGER NOT NULL,
            codigo_patrimonial TEXT NOT NULL,
            nombre_bien TEXT NOT NULL,
            persona_anterior TEXT NOT NULL,
            persona_nueva TEXT NOT NULL,
            motivo TEXT NOT NULL,
            fecha TEXT NOT NULL,
            FOREIGN KEY (bien_id) REFERENCES bienes(id)
        )
    """)

    conn.commit()
    conn.close()


@app.route("/")
def home():
    return "Backend del sistema de bienes funcionando correctamente"


@app.route("/registrar_bien", methods=["POST"])
def registrar_bien():
    try:
        data = request.get_json()

        codigo_patrimonial = data.get("codigo_patrimonial", "").strip()
        nombre = data.get("nombre", "").strip()
        descripcion = data.get("descripcion", "").strip()
        estado = data.get("estado", "").strip()
        persona_asignada = data.get("persona_asignada", "").strip()

        if not codigo_patrimonial or not nombre or not descripcion or not estado or not persona_asignada:
            return jsonify({
                "ok": False,
                "mensaje": "Todos los campos son obligatorios"
            }), 400

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id FROM bienes WHERE codigo_patrimonial = ?
        """, (codigo_patrimonial,))
        existente = cursor.fetchone()

        if existente:
            conn.close()
            return jsonify({
                "ok": False,
                "mensaje": "El código patrimonial ya existe"
            }), 400

        cursor.execute("""
            INSERT INTO bienes (
                codigo_patrimonial,
                nombre,
                descripcion,
                estado,
                persona_asignada
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            codigo_patrimonial,
            nombre,
            descripcion,
            estado,
            persona_asignada
        ))

        conn.commit()
        conn.close()

        return jsonify({
            "ok": True,
            "mensaje": "Bien registrado correctamente"
        })

    except Exception as e:
        return jsonify({
            "ok": False,
            "mensaje": f"Error interno: {str(e)}"
        }), 500


@app.route("/bienes", methods=["GET"])
def listar_bienes():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM bienes
            ORDER BY id DESC
        """)
        filas = cursor.fetchall()

        bienes = [dict(fila) for fila in filas]

        conn.close()

        return jsonify(bienes)

    except Exception as e:
        return jsonify({
            "ok": False,
            "mensaje": f"Error al listar bienes: {str(e)}"
        }), 500


@app.route("/importar_excel", methods=["POST"])
def importar_excel():
    try:
        if "archivo" not in request.files:
            return jsonify({
                "ok": False,
                "mensaje": "No se envió ningún archivo"
            }), 400

        archivo = request.files["archivo"]

        if archivo.filename == "":
            return jsonify({
                "ok": False,
                "mensaje": "Debe seleccionar un archivo Excel"
            }), 400

        df = pd.read_excel(archivo)

        columnas_esperadas = [
            "codigo_patrimonial",
            "nombre",
            "descripcion",
            "estado",
            "persona_asignada"
        ]

        for columna in columnas_esperadas:
            if columna not in df.columns:
                return jsonify({
                    "ok": False,
                    "mensaje": f"Falta la columna obligatoria: {columna}"
                }), 400

        conn = get_connection()
        cursor = conn.cursor()

        registrados = 0
        duplicados = 0
        incompletos = 0

        for _, row in df.iterrows():
            codigo = str(row["codigo_patrimonial"]).strip()
            nombre = str(row["nombre"]).strip()
            descripcion = str(row["descripcion"]).strip()
            estado = str(row["estado"]).strip()
            persona = str(row["persona_asignada"]).strip()

            if (
                not codigo or codigo.lower() == "nan" or
                not nombre or nombre.lower() == "nan" or
                not descripcion or descripcion.lower() == "nan" or
                not estado or estado.lower() == "nan" or
                not persona or persona.lower() == "nan"
            ):
                incompletos += 1
                continue

            cursor.execute("""
                SELECT id FROM bienes WHERE codigo_patrimonial = ?
            """, (codigo,))
            existe = cursor.fetchone()

            if existe:
                duplicados += 1
                continue

            cursor.execute("""
                INSERT INTO bienes (
                    codigo_patrimonial,
                    nombre,
                    descripcion,
                    estado,
                    persona_asignada
                )
                VALUES (?, ?, ?, ?, ?)
            """, (codigo, nombre, descripcion, estado, persona))

            registrados += 1

        conn.commit()
        conn.close()

        return jsonify({
            "ok": True,
            "mensaje": "Importación completada",
            "registrados": registrados,
            "duplicados": duplicados,
            "incompletos": incompletos
        })

    except Exception as e:
        return jsonify({
            "ok": False,
            "mensaje": f"Error al importar Excel: {str(e)}"
        }), 500


@app.route("/desplazar_bienes", methods=["POST"])
def desplazar_bienes():
    try:
        data = request.get_json()

        bienes_ids = data.get("bienes_ids", [])
        nueva_persona = data.get("nueva_persona", "").strip()
        motivo = data.get("motivo", "").strip()

        if not bienes_ids or len(bienes_ids) == 0:
            return jsonify({
                "ok": False,
                "mensaje": "Debe seleccionar al menos un bien"
            }), 400

        if not nueva_persona:
            return jsonify({
                "ok": False,
                "mensaje": "La nueva persona es obligatoria"
            }), 400

        if not motivo:
            return jsonify({
                "ok": False,
                "mensaje": "El motivo es obligatorio"
            }), 400

        conn = get_connection()
        cursor = conn.cursor()

        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        actualizados = 0

        for bien_id in bienes_ids:
            cursor.execute("""
                SELECT * FROM bienes WHERE id = ?
            """, (bien_id,))
            bien = cursor.fetchone()

            if not bien:
                continue

            persona_anterior = bien["persona_asignada"]

            if persona_anterior.strip().lower() == nueva_persona.strip().lower():
                continue

            cursor.execute("""
                UPDATE bienes
                SET persona_asignada = ?
                WHERE id = ?
            """, (nueva_persona, bien_id))

            cursor.execute("""
                INSERT INTO historial (
                    bien_id,
                    codigo_patrimonial,
                    nombre_bien,
                    persona_anterior,
                    persona_nueva,
                    motivo,
                    fecha
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                bien["id"],
                bien["codigo_patrimonial"],
                bien["nombre"],
                persona_anterior,
                nueva_persona,
                motivo,
                fecha_actual
            ))

            actualizados += 1

        conn.commit()
        conn.close()

        return jsonify({
            "ok": True,
            "mensaje": f"Se desplazaron {actualizados} bienes correctamente"
        })

    except Exception as e:
        return jsonify({
            "ok": False,
            "mensaje": f"Error al desplazar bienes: {str(e)}"
        }), 500


@app.route("/historial", methods=["GET"])
def listar_historial():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM historial
            ORDER BY id DESC
        """)
        filas = cursor.fetchall()

        historial = [dict(fila) for fila in filas]

        conn.close()

        return jsonify(historial)

    except Exception as e:
        return jsonify({
            "ok": False,
            "mensaje": f"Error al obtener historial: {str(e)}"
        }), 500


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)