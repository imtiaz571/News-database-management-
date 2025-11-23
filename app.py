from flask import Flask, render_template, jsonify, request
import mysql.connector
import mysql.connector
from mysql.connector import Error
import threading
import urllib.request
import urllib.parse
import os
import time

app = Flask(__name__)

# --- CONFIGURATION ---
# Database configuration specifically for XAMPP Port 3307
DB_CONFIG = {
    'host': 'localhost',
    'database': 'news_blog_db',
    'user': 'root',
    'password': '',
    'port': 3307
}

def get_db_connection():
    """Establishes a connection to the database."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

# --- BACKGROUND TASKS ---
def generate_news_image(news_id, title, body):
    """Generates an image for the news item in the background."""
    print(f"[{news_id}] Starting background image generation...")
    
    try:
        # 1. Construct Prompt
        prompt = f"{title} {body[:50]}".strip()
        encoded_prompt = urllib.parse.quote(prompt)
        image_url = f"https://pollinations.ai/p/{encoded_prompt}?width=800&height=400&seed={news_id}&model=flux"
        
        # 2. Define Paths
        filename = f"news_{news_id}.jpg"
        static_dir = os.path.join(app.root_path, 'static', 'news_images')
        if not os.path.exists(static_dir):
            os.makedirs(static_dir)
            
        file_path = os.path.join(static_dir, filename)
        
        # 3. Download Image
        print(f"[{news_id}] Downloading from: {image_url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://pollinations.ai/',
            'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'
        }
        req = urllib.request.Request(image_url, headers=headers)
        
        with urllib.request.urlopen(req) as response, open(file_path, 'wb') as out_file:
            out_file.write(response.read())
            
        print(f"[{news_id}] Image saved to: {file_path}")
        
        # 4. Update Database
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        db_image_path = f"/static/news_images/{filename}"
        cursor.execute("UPDATE news SET image_url = %s WHERE news_id = %s", (db_image_path, news_id))
        conn.commit()
        cursor.close()
        conn.close()
        print(f"[{news_id}] Database updated with image.")
        
    except Exception as e:
        with open("debug_log.txt", "a") as f:
            f.write(f"[{news_id}] ERROR: {e}\n")
        print(f"[{news_id}] ERROR generating image: {e}")

# --- ROUTING (VIEW) ---

@app.route('/')
def index():
    """Serves the single-page frontend."""
    return render_template('index.html')

# --- API CONTROLLERS ---

@app.route('/api/users', methods=['GET', 'POST'])
def handle_users():
    conn = get_db_connection()
    if not conn: return jsonify({'error': 'Database connection failed'}), 500
   
    cursor = conn.cursor(dictionary=True)
   
    try:
        if request.method == 'GET':
            cursor.execute("SELECT * FROM users ORDER BY user_id DESC")
            users = cursor.fetchall()
            return jsonify(users)
       
        if request.method == 'POST':
            data = request.json
            query = "INSERT INTO users (username, email, age, contact_number) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (data['username'], data['email'], data['age'], data['contact_number']))
            conn.commit()
            return jsonify({'message': 'User created', 'id': cursor.lastrowid}), 201
           
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/users/<int:user_id>', methods=['PUT', 'DELETE'])
def handle_single_user(user_id):
    conn = get_db_connection()
    if not conn: return jsonify({'error': 'Database connection failed'}), 500
   
    cursor = conn.cursor(dictionary=True)

    try:
        if request.method == 'PUT':
            data = request.json
            query = "UPDATE users SET username=%s, email=%s, age=%s, contact_number=%s WHERE user_id=%s"
            cursor.execute(query, (data['username'], data['email'], data['age'], data['contact_number'], user_id))
            conn.commit()
            return jsonify({'message': 'User updated'})

        if request.method == 'DELETE':
            # Note: ON DELETE CASCADE in DB schema handles the news deletion automatically
            cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
            conn.commit()
            return jsonify({'message': 'User deleted'})
           
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/news', methods=['GET', 'POST'])
def handle_news():
    conn = get_db_connection()
    if not conn: return jsonify({'error': 'Database connection failed'}), 500
    cursor = conn.cursor(dictionary=True)

    try:
        if request.method == 'GET':
            # JOIN query to get the author username
            query = """
                SELECT news.*, users.username
                FROM news
                JOIN users ON news.user_id = users.user_id
                ORDER BY created_at DESC
            """
            cursor.execute(query)
            news = cursor.fetchall()
            return jsonify(news)

        if request.method == 'POST':
            data = request.json
            print(f"DEBUG: Received news data: {data}") # Debug log
            
            if 'user_id' not in data:
                print("ERROR: user_id missing in request data")
                return jsonify({'error': 'user_id is required'}), 400

            query = "INSERT INTO news (title, body, user_id) VALUES (%s, %s, %s)"
            cursor.execute(query, (data['title'], data['body'], data['user_id']))
            conn.commit()
            
            # Start Background Image Generation
            news_id = cursor.lastrowid
            thread = threading.Thread(target=generate_news_image, args=(news_id, data['title'], data['body']))
            thread.start()
            
            print("DEBUG: News inserted successfully, background task started.")
            return jsonify({'message': 'News added'}), 201

    except Exception as e: # Catch all exceptions
        print(f"ERROR in handle_news: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/news/<int:news_id>', methods=['PUT', 'DELETE'])
def handle_news_item(news_id):
    conn = get_db_connection()
    if not conn: return jsonify({'error': 'Database connection failed'}), 500
    cursor = conn.cursor()

    try:
        if request.method == 'PUT':
            data = request.json
            query = "UPDATE news SET title=%s, body=%s WHERE news_id=%s"
            cursor.execute(query, (data['title'], data['body'], news_id))
            conn.commit()
           
        if request.method == 'DELETE':
            cursor.execute("DELETE FROM news WHERE news_id=%s", (news_id,))
            conn.commit()
           
        return jsonify({'message': 'Success'})
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/users/<int:user_id>/news', methods=['GET'])
def get_user_news(user_id):
    conn = get_db_connection()
    if not conn: return jsonify({'error': 'Database connection failed'}), 500
    cursor = conn.cursor(dictionary=True)
   
    try:
        cursor.execute("SELECT * FROM news WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
        news = cursor.fetchall()
        return jsonify(news)
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    # Debug mode enabled for development
    app.run(debug=True, port=5000)
