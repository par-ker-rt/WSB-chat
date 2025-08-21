import sqlite3
from pathlib import Path


DB = Path('wsb.db')
if DB.exists():
print('db exists')
else:
conn = sqlite3.connect('wsb.db')
c = conn.cursor()
c.execute('''CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, email TEXT, password TEXT, tier TEXT, days_left INTEGER)''')
c.execute('''CREATE TABLE posts (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, title TEXT, content TEXT, author TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
c.execute('''CREATE TABLE groups (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, owner TEXT, members TEXT)''')
c.execute('INSERT INTO users (username,email,password,tier,days_left) VALUES (?,?,?,?,?)', ('admin','admin@local','2518','admin',9999))
conn.commit()
conn.close()
print('db created with admin/admin@local/2518')
