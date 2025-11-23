import mysql.connector

# Configuration from app.py
DB_CONFIG = {
    'host': 'localhost',
    'database': 'news_blog_db',
    'user': 'root',
    'password': '',
    'port': 3307
}

def migrate():
    print("--- Starting Database Migration ---")
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("SHOW COLUMNS FROM news LIKE 'image_url'")
        result = cursor.fetchone()
        
        if not result:
            print("Adding 'image_url' column to 'news' table...")
            cursor.execute("ALTER TABLE news ADD COLUMN image_url VARCHAR(500) DEFAULT NULL")
            conn.commit()
            print("SUCCESS: Column added.")
        else:
            print("INFO: 'image_url' column already exists.")
            
    except mysql.connector.Error as e:
        print(f"ERROR: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("Connection closed.")

if __name__ == "__main__":
    migrate()
