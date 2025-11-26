import mysql.connector
import random



db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'port': 3307
}

def init_db():
    print("--- Starting Database Initialization ---")
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

     
        cursor.execute("CREATE DATABASE IF NOT EXISTS news_blog_db")
        cursor.execute("USE news_blog_db")
        print("[+] Database selected.")

       
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL,
            age INT,
            contact_number VARCHAR(20)
        )
        """)
        print("[+] Users table ready.")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS news (
            news_id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            body TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            user_id INT,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
        """)
        print("[+] News table ready.")

      
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            print("[*] Seeding data (10 Users, 30 News items)...")
           
            
            users_data = []
            for i in range(1, 11):
                users_data.append((f"User_{i}", f"user{i}@test.com", random.randint(20, 50), f"555-010{i}"))
           
            cursor.executemany("INSERT INTO users (username, email, age, contact_number) VALUES (%s, %s, %s, %s)", users_data)
            conn.commit()

            cursor.execute("SELECT user_id FROM users")
            user_ids = [row[0] for row in cursor.fetchall()]

            
            news_data = []
            topics = ["Python", "SQL", "Flask", "Web Design", "AI", "Data Science"]
            for uid in user_ids:
                for j in range(3):
                    topic = random.choice(topics)
                    title = f"{topic} Update - Post {j+1}"
                    body = f"This is an automated post about {topic}. It serves as placeholder content for the database assignment."
                    news_data.append((title, body, uid))

            cursor.executemany("INSERT INTO news (title, body, user_id) VALUES (%s, %s, %s)", news_data)
            conn.commit()
            print("[+] Data seeding complete.")
        else:
            print("[-] Data already exists. Skipping seed.")

        cursor.close()
        conn.close()
        print("--- Initialization Success ---")

    except mysql.connector.Error as err:
        print(f"FAILED: {err}")
        print("Ensure XAMPP is running on Port 3307.")

if __name__ == "__main__":
    init_db()
