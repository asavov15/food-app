import sqlite3
import os

print("Running init_db.py from:", os.getcwd())

connection = sqlite3.connect("spots.db")

with open("schema.sql") as f:
    sql = f.read()
    print("Loaded schema.sql:")
    print(sql)
    connection.executescript(sql)

connection.commit()
connection.close()

print("Database initialized.")