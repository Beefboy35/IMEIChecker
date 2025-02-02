import sqlite3

# whitelist.db находится в корневой папке
conn = sqlite3.connect('../telebot.db')


cursor = conn.cursor()


cursor.execute('''
CREATE TABLE IF NOT EXISTS whitelist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL

)
''')

print(cursor.execute('''select * FROM whitelist''').fetchall())

conn.commit()
conn.close()