import sqlite3
db_path = "databaseUser"

def create_connection(db_file = db_path):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except sqlite3.Error as e:
        print(e)

    return conn
