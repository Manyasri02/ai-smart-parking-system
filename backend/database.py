import sqlite3

DB_NAME = "parking.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # return rows as dict-like
    return conn
