import urllib.request
import urllib.parse
import json
import time
import mysql.connector
import os

# Config
BASE_URL = 'http://127.0.0.1:5000/api'
DB_CONFIG = {
    'host': 'localhost',
    'database': 'news_blog_db',
    'user': 'root',
    'password': '',
    'port': 3307
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def test_image_generation():
    print("--- Testing Background Image Generation ---")
    
    # 1. Create a User (if needed) or get existing
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users LIMIT 1")
        user = cursor.fetchone()
        if not user:
            print("Creating test user...")
            cursor.execute("INSERT INTO users (username, email) VALUES ('TestUser', 'test@example.com')")
            conn.commit()
            user_id = cursor.lastrowid
        else:
            user_id = user[0]
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"DB Error: {e}")
        return

    # 2. Post News
    print(f"Posting news for User ID: {user_id}")
    payload = {
        'title': 'The Future of AI',
        'body': 'Artificial Intelligence is rapidly evolving, creating stunning images and text.',
        'user_id': user_id
    }
    
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(f"{BASE_URL}/news", data=data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as response:
            if response.status != 201:
                print(f"FAILED to post news: {response.read().decode()}")
                return
            print("News posted successfully. Waiting for background generation (15s)...")
        
        time.sleep(15) # Wait for thread
        
        # 3. Verify DB Update
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM news WHERE title = %s ORDER BY created_at DESC LIMIT 1", (payload['title'],))
        news_item = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not news_item:
            print("FAILED: News item not found in DB.")
            return
            
        print(f"News Item Found: ID {news_item['news_id']}")
        image_url = news_item.get('image_url')
        print(f"Image URL: {image_url}")
        
        if image_url and image_url.startswith('/static/news_images/'):
            # 4. Verify File Existence
            file_path = os.path.join(os.getcwd(), image_url.lstrip('/'))
            # Fix path separators for Windows
            file_path = file_path.replace('/', os.sep)
            
            if os.path.exists(file_path):
                print(f"SUCCESS: Image file exists at {file_path}")
            else:
                print(f"FAILED: Image file missing at {file_path}")
        else:
            print("FAILED: image_url is missing or invalid.")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_image_generation()
