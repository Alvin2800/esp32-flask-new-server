from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)

# Railway : utiliser un chemin explicite
DB_DIR = os.getenv("DB_DIR", "/app/data")
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "database.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS measurements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        temperature REAL NOT NULL,
        humidity REAL NOT NULL,
        emergency INTEGER NOT NULL
    )
    """)

    conn.commit()
    conn.close()


init_db()


def insert_data(timestamp, temperature, humidity, emergency):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO measurements (timestamp, temperature, humidity, emergency)
        VALUES (?, ?, ?, ?)
    """, (timestamp, temperature, humidity, emergency))

    conn.commit()
    conn.close()


@app.route("/")
def home():
    return "IoT API Alvin Running", 200


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/data", methods=["GET"])
def data():
    try:
        temp_raw = request.args.get("temp")
        hum_raw = request.args.get("hum")
        emergency_raw = request.args.get("emergency", "0")

        if temp_raw is None or hum_raw is None:
            return jsonify({"error": "Missing temp or hum parameter"}), 400

        temperature = float(temp_raw)
        humidity = float(hum_raw)
        emergency = int(emergency_raw)

        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        insert_data(timestamp, temperature, humidity, emergency)

        payload = {
            "timestamp": timestamp,
            "temperature": temperature,
            "humidity": humidity,
            "emergency": emergency
        }

        print(f"Données reçues : {payload}", flush=True)
        return jsonify({"message": "OK", "data": payload}), 200

    except Exception as e:
        print(f"Erreur /data : {e}", flush=True)
        return jsonify({"error": str(e)}), 500


@app.route("/status")
def status():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT timestamp, temperature, humidity, emergency
            FROM measurements
            ORDER BY id DESC
            LIMIT 1
        """)
        row = cursor.fetchone()
        conn.close()

        if row is None:
            return jsonify({
                "temperature": None,
                "humidity": None,
                "emergency": None,
                "timestamp": None
            }), 200

        return jsonify({
            "timestamp": row["timestamp"],
            "temperature": row["temperature"],
            "humidity": row["humidity"],
            "emergency": row["emergency"]
        }), 200

    except Exception as e:
        print(f"Erreur /status : {e}", flush=True)
        return jsonify({"error": str(e)}), 500


@app.route("/logs")
def get_logs():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT timestamp, temperature, humidity, emergency
            FROM measurements
            ORDER BY id DESC
            LIMIT 100
        """)

        rows = cursor.fetchall()
        conn.close()

        logs = []
        for row in rows:
            logs.append({
                "timestamp": row["timestamp"],
                "temperature": row["temperature"],
                "humidity": row["humidity"],
                "emergency": row["emergency"]
            })

        return jsonify(logs), 200

    except Exception as e:
        print(f"Erreur /logs : {e}", flush=True)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
