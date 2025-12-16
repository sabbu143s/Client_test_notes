import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024 # <--- Allow 500MB uploads

# ⚠️ ENSURE THIS IS YOUR CORRECT INTERNAL DATABASE URL
# It usually starts with postgres://...
DB_URL = os.environ.get("DATABASE_URL") 
# If you didn't set the Env Var in Render, paste the hardcoded string here:
# DB_URL = "postgres://client_db_5b7x_user:..."

def get_db():
    return psycopg2.connect(DB_URL)

def create_tables():
    """Function to create the table"""
    conn = get_db()
    with conn.cursor() as cur:
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

# ==================== 1. NEW INIT ENDPOINT ====================
@app.route('/init-db', methods=['GET'])
def manual_db_init():
    try:
        create_tables()
        return jsonify({"message": "✅ Success! Table 'client_media_notes' created."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== 2. STORE ENDPOINT ====================
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

# ==================== 3. FETCH ENDPOINT ====================
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
        # If table missing, return helpful error
        if 'does not exist' in str(e):
             return jsonify({"error": "Table missing. Please go to /init-db first!"}), 500
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
