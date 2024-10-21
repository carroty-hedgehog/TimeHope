import sqlite3

#Создаем соединение с базой данных
conn = sqlite3.connect('posts.db')
cursor = conn.cursor()

#Создаем таблицу для хранения постов
cursor.execute('''
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    text TEXT,
    hashtags TEXT
)
''')

#Закрываем соединение
conn.commit()
conn.close()
