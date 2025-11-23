import mysql.connector
from mysql.connector import Error

# Same config as app.py
DB_CONFIG = {
    'host': 'localhost',
    'database': 'news_blog_db',
    'user': 'root',
    'password': '',
    'port': 3307
}

def check_data():
    print(f"Connecting to database on port {DB_CONFIG['port']}...")
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        if conn.is_connected():
            print("Connected successfully.")
            cursor = conn.cursor(dictionary=True)
            
            print("\n--- Latest 5 News Items ---")
            cursor.execute("SELECT news_id, title, created_at, user_id FROM news ORDER BY created_at DESC LIMIT 5")
            rows = cursor.fetchall()
            if not rows:
                print("No news items found.")
            else:
                for row in rows:
                    print(row)
                    
            print("\n--- Latest 5 Users ---")
            cursor.execute("SELECT user_id, username FROM users ORDER BY user_id DESC LIMIT 5")
            rows = cursor.fetchall()
            for row in rows:
                print(row)

            cursor.close()
            conn.close()
    except Error as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_data()
