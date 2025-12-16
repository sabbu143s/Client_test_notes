import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ⚠️ PASTE YOUR 2ND RENDER POSTGRES URL HERE
# In production, use os.getenv("DATABASE_URL")
DB_URL = "postgresql://client_db_5b7x_user:CYIQSwVZ4B5GrpgFg7EzJrJzSbNQNpBf@dpg-d4vua3i4d50c7389bo7g-a/client_db_5b7x"

def get_db():
    return psycopg2.connect(DB_URL)

def init_db():
    conn = get_db()
    with conn.cursor() as cur:
        # We store 'media_type' so the frontend knows if it's an image or video later
        cur.execute("""
            CREATE TABLE IF NOT EXISTS client_media_notes (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(100),
                title VARCHAR(255),
                media_type VARCHAR(50), 
                encrypted_blob TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
    conn.close()

@app.route('/api/store', methods=['POST'])
def store_note():
    data = request.json
    try:
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO client_media_notes (user_id, title, media_type, encrypted_blob) VALUES (%s, %s, %s, %s) RETURNING id",
                (data['user_id'], data['title'], data['media_type'], data['encrypted_blob'])
            )
            new_id = cur.fetchone()[0]
            conn.commit()
        conn.close()
        return jsonify({"status": "success", "id": new_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/fetch/<user_id>', methods=['GET'])
def fetch_notes(user_id):
    try:
        conn = get_db()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM client_media_notes WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
            rows = cur.fetchall()
        conn.close()
        return jsonify(rows), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    try:
        init_db()
        print("✅ Storage DB Connected & Initialized")
    except Exception as e:
        print(f"❌ DB Error: {e}")
    
    app.run(host='0.0.0.0', port=5002)
