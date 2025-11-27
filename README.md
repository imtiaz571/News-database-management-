# NAUU News Portal

A modern, Flask-based news portal application featuring user management, real-time news updates, and AI-powered image generation for articles.

## Features

-   **User Management**: Create, read, update, and delete user profiles.
-   **News Management**: Users can publish, edit, and delete news stories.
-   **AI Image Generation**: Automatically generates relevant images for news articles using the Pollinations.ai API based on the article title and content.
-   **Modern UI**: Responsive design built with Tailwind CSS, featuring a dark mode aesthetic and glassmorphism effects.
-   **Search & Filter**: Filter news by categories (Tech, Design) and search for stories or users.
-   **Interactive Interface**: Modal-based interactions for reading news and managing profiles.

### System Workflow
The diagram below illustrates how the backend manages news submission and asynchronous AI image generation.

![System Workflow Sequence Diagram](Untitled%20diagram-2025-11-26-195928.jpg)

## Technology Stack

-   **Backend**: Python, Flask
-   **Database**: MySQL (configured for XAMPP)
-   **Frontend**: HTML5, Tailwind CSS (via CDN), Vanilla JavaScript
-   **External APIs**: Pollinations.ai (for image generation)

## Prerequisites

-   Python 3.x
-   MySQL Server (XAMPP recommended)
-   pip (Python package manager)

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Install Python dependencies:**
    ```bash
    pip install flask mysql-connector-python
    ```

3.  **Database Setup:**
    
    The application uses a relational database to manage Users and News. Refer to the ER diagram below for the schema structure:

    ![Database ER Diagram](Untitled%20diagram-2025-11-27-033350.png)

    -   Ensure your MySQL server is running (default configuration expects XAMPP on port 3307).
    -   Create a database named `news_blog_db`.
    -   Import the necessary tables. You can use the provided `database_setup.py` script if available, or manually create the tables:

    ```sql
    CREATE DATABASE IF NOT EXISTS news_blog_db;
    USE news_blog_db;

    CREATE TABLE IF NOT EXISTS users (
        user_id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL,
        age INT,
        contact_number VARCHAR(20)
    );

    CREATE TABLE IF NOT EXISTS news (
        news_id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        body TEXT NOT NULL,
        image_url VARCHAR(500),
        user_id INT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    ```

4.  **Configuration:**
    -   Open `app.py` and check the `DB_CONFIG` dictionary.
    -   Update the `host`, `user`, `password`, and `port` to match your MySQL configuration if different from the defaults.

    ```python
    DB_CONFIG = {
        'host': 'localhost',
        'database': 'news_blog_db',
        'user': 'root',
        'password': '',
        'port': 3307  # Default XAMPP MySQL port
    }
    ```

## Usage

1.  **Run the application:**
    ```bash
    python app.py
    ```

2.  **Access the portal:**
    -   Open your web browser and navigate to `http://127.0.0.1:5000`.

3.  **Interact:**
    -   Click "+ Create User" to add a new user.
    -   Select a user from the "Community" sidebar to view their profile or post news.
    -   Click on any news card to read the full story.

## Project Structure

-   `app.py`: Main Flask application file containing API endpoints and logic.
-   `templates/index.html`: Single-page frontend application.
-   `static/`: Directory for storing generated images and other static assets.
-   `check_db.py` & `database_setup.py`: Utility scripts for database management.
