import sqlite3

def setup_database():
    conn = sqlite3.connect('content.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS serp_data (
            id INTEGER PRIMARY KEY,
            keyword TEXT,
            title TEXT,
            url TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY,
            keyword TEXT,
            title TEXT,
            meta_description TEXT,
            content TEXT
        )
    ''')
    conn.commit()
    conn.close()

def store_serp_results(keyword, results):
    conn = sqlite3.connect('content.db')
    cursor = conn.cursor()
    for title, url in results:
        cursor.execute("INSERT INTO serp_data (keyword, title, url) VALUES (?, ?, ?)", (keyword, title, url))
    conn.commit()
    conn.close()

def save_article(keyword, title, meta_description, content):
    conn = sqlite3.connect('content.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO articles (keyword, title, meta_description, content) VALUES (?, ?, ?, ?)",
        (keyword, title, meta_description, content)
    )
    conn.commit()
    conn.close()
