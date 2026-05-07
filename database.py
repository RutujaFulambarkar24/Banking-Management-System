import sqlite3

def connect_db():
    return sqlite3.connect("bank.db", check_same_thread=False)


def create_table():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        phone TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        balance REAL,
        account_type TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id INTEGER,
        type TEXT,
        amount REAL,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS loans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        amount REAL,
        interest REAL,
        status TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)
    
    cursor.execute("""
    INSERT OR IGNORE INTO admins (username, password)
    VALUES ('admin', '1234')
    """)

    conn.commit()
    conn.close()