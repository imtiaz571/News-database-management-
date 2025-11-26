from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import mysql.connector
from mysql.connector import Error
import threading
import urllib.request
import urllib.parse
import os
import time
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = '1234'  

# --- CONFIGURATION ---
# Database configuration specifically for XAMPP Port 3307
DB_CONFIG = {
    'host': 'localhost',
    'database': 'news_blog_db',
    'user': 'root',
    'password': '',
    'port': 3307
}

# --- FLASK LOGIN SETUP ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_page'

class User(UserMixin):
    def __init__(self, user_id, username, email, role='user'):
        self.id = user_id
        self.username = username
        self.email = email
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    if not conn: return None
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        user_data = cursor.fetchone()
        if user_data:
            return User(user_data['user_id'], user_data['username'], user_data['email'])
        return None
    finally:
        cursor.close()
        conn.close()

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
    
    models = ['flux', 'turbo']
    success = False
    
    for model in models:
        if success: break
        try:
            print(f"[{news_id}] Trying model: {model}")
            # 1. Construct Prompt
            prompt = f"{title} {body[:50]}".strip()
            encoded_prompt = urllib.parse.quote(prompt)
            image_url = f"https://pollinations.ai/p/{encoded_prompt}?width=800&height=400&seed={news_id}&model={model}"
            
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
            
            # Set a timeout to prevent hanging
            with urllib.request.urlopen(req, timeout=30) as response, open(file_path, 'wb') as out_file:
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
            success = True
            
        except Exception as e:
            print(f"[{news_id}] Model {model} failed: {e}")
            with open("debug_log.txt", "a") as f:
                f.write(f"[{news_id}] ERROR with {model}: {e}\n")
    
    if not success:
        print(f"[{news_id}] All image generation attempts failed.")

# --- ROUTING (VIEW) ---

@app.route('/')
@login_required
def index():
    """Serves the single-page frontend."""
    return render_template('index.html', current_user=current_user)

@app.route('/login')
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return render_template('login.html')

# --- AUTH API ---

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    conn = get_db_connection()
    if not conn: return jsonify({'error': 'Database connection failed'}), 500
    cursor = conn.cursor()
    try:
        # Check if user exists
        cursor.execute("SELECT user_id FROM users WHERE username = %s OR email = %s", (data['username'], data['email']))
        if cursor.fetchone():
            return jsonify({'error': 'Username or Email already exists'}), 400

        hashed_password = generate_password_hash(data['password'])
        query = "INSERT INTO users (username, email, password_hash, age, contact_number) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (data['username'], data['email'], hashed_password, data.get('age'), data.get('contact_number')))
        conn.commit()
        
        user_id = cursor.lastrowid
        user = User(user_id, data['username'], data['email'])
        login_user(user)
        
        return jsonify({'message': 'Registered successfully', 'user': {'id': user_id, 'username': user.username}}), 201
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    conn = get_db_connection()
    if not conn: return jsonify({'error': 'Database connection failed'}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users WHERE username = %s", (data['username'],))
        user_data = cursor.fetchone()
        
        if user_data and user_data['password_hash'] and check_password_hash(user_data['password_hash'], data['password']):
            user = User(user_data['user_id'], user_data['username'], user_data['email'])
            login_user(user)
            return jsonify({'message': 'Logged in successfully', 'user': {'id': user.id, 'username': user.username}})
        
        return jsonify({'error': 'Invalid username or password'}), 401
    finally:
        cursor.close()
        conn.close()

@app.route('/api/auth/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully'})

@app.route('/api/auth/me', methods=['GET'])
def get_current_user():
    if current_user.is_authenticated:
        return jsonify({'authenticated': True, 'user': {'id': current_user.id, 'username': current_user.username}})
    return jsonify({'authenticated': False})

# --- API CONTROLLERS ---

@app.route('/api/users', methods=['GET', 'POST'])
@login_required
def handle_users():
    conn = get_db_connection()
    if not conn: return jsonify({'error': 'Database connection failed'}), 500
   
    cursor = conn.cursor(dictionary=True)
   
    try:
        if request.method == 'GET':
            cursor.execute("SELECT user_id, username, email, age, contact_number FROM users ORDER BY user_id DESC")
            users = cursor.fetchall()
            return jsonify(users)
       
        if request.method == 'POST':
            # Admin or internal creation? For now, let's assume this is legacy or admin only.
            # But the user asked for "login page where a user have to login first... and upload news".
            # So normal users register via /api/auth/register.
            # This endpoint might be redundant for creation if we enforce auth.
            # Let's keep it but require auth.
            data = request.json
            # Note: This doesn't handle password hashing if used directly. 
            # Ideally, we should deprecate this for creation or update it.
            # For now, I'll leave it but it won't set a password.
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
@login_required
def handle_single_user(user_id):
    # Ensure user can only edit themselves unless admin (no admin role yet)
    if current_user.id != user_id:
         return jsonify({'error': 'Unauthorized'}), 403

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
            logout_user() # Logout if deleting self
            return jsonify({'message': 'User deleted'})
           
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/news', methods=['GET', 'POST'])
@login_required
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
            
            # Enforce current user
            user_id = current_user.id

            query = "INSERT INTO news (title, body, user_id) VALUES (%s, %s, %s)"
            cursor.execute(query, (data['title'], data['body'], user_id))
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
@login_required
def handle_news_item(news_id):
    conn = get_db_connection()
    if not conn: return jsonify({'error': 'Database connection failed'}), 500
    cursor = conn.cursor(dictionary=True)

    try:
        # Check ownership
        cursor.execute("SELECT user_id FROM news WHERE news_id = %s", (news_id,))
        news_item = cursor.fetchone()
        if not news_item:
            return jsonify({'error': 'News not found'}), 404
            
        if news_item['user_id'] != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403

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
@login_required
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

