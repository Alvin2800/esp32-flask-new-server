from flask import Flask, request, jsonify
import mysql.connector
from datetime import datetime
import os

app = Flask(__name__)

# 🔹 Config MySQL via variables Railway
db_config = {
    "host": os.getenv("MYSQLHOST"),
    "user": os.getenv("MYSQLUSER"),
    "password": os.getenv("MYSQLPASSWORD"),
    "database": os.getenv("MYSQLDATABASE"),
    "port": int(os.getenv("MYSQLPORT", 3306))
}

# 🔹 Connexion DB
def get_db_connection():
    return mysql.connector.connect(**db_config)

# 🔹 Initialisation DB dès le démarrage
def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS measurements (
            id INT AUTO_INCREMENT PRIMARY KEY,
            timestamp DATETIME NOT NULL,
            temperature FLOAT NOT NULL,
            humidity FLOAT NOT NULL,
            emergency INT NOT NULL
        )
        """)

        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Base de données prête", flush=True)

    except Exception as e:
        print("❌ Erreur DB init :", e, flush=True)

# ✅ appel ici, hors du __main__
init_db()

# 🔹 Insertion données
def insert_data(timestamp, temperature, humidity, emergency):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            INSERT INTO measurements (timestamp, temperature, humidity, emergency)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (timestamp, temperature, humidity, emergency))
        conn.commit()
        cursor.close()
        conn.close()

    except Exception as e:
        print("❌ Erreur insertion :", e, flush=True)

# 🔹 Variables globales
temperature = 0.0
humidity = 0.0
emergency = 0

# 🔹 Home
@app.route("/")
def home():
    return "IoT API Alvin Running (MySQL 🚀)"

# 🔹 Endpoint ESP32
@app.route("/data")
def data():
    global temperature, humidity, emergency
    try:
        temperature = float(request.args.get("temp", 0))
        humidity = float(request.args.get("hum", 0))
        emergency = int(request.args.get("emergency", 0))

        timestamp = datetime.now()

        insert_data(timestamp, temperature, humidity, emergency)

        print("📡 Données reçues :", {
            "timestamp": timestamp,
            "temperature": temperature,
            "humidity": humidity,
            "emergency": emergency
        }, flush=True)

        return "OK", 200

    except Exception as e:
        print("❌ Erreur /data :", e, flush=True)
        return "Erreur", 500

# 🔹 Status temps réel
@app.route("/status")
def status():
    return jsonify({
        "temperature": temperature,
        "humidity": humidity,
        "emergency": emergency
    })

# 🔹 Logs depuis MySQL
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
        cursor.close()
        conn.close()

        logs = []
        for row in rows:
            logs.append({
                "timestamp": str(row[0]),
                "temperature": row[1],
                "humidity": row[2],
                "emergency": row[3]
            })

        return jsonify(logs)
@app.route("/test-db")
def test_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({"tables": tables})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    except Exception as e:
        print("❌ Erreur /logs :", e, flush=True)
        return jsonify({"error": "Erreur récupération données"}), 500

# 🔹 Lancement serveur
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
