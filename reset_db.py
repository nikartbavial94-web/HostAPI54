import sqlite3
import os

# Удаляем старую базу данных если существует
if os.path.exists('school.db'):
    os.remove('school.db')
    print("Старая база данных удалена")

# Создаем новую базу с полем day_of_week
conn = sqlite3.connect('school.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE lessons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_number INTEGER NOT NULL,
        class_letter TEXT NOT NULL,
        classroom TEXT NOT NULL,
        lesson_number INTEGER NOT NULL,
        teacher TEXT NOT NULL,
        day_of_week TEXT NOT NULL
    )
''')

# Добавляем тестовые данные
test_lessons = [
    (5, 'А', '201', 1, 'Иванова М.И.', 'monday'),
    (5, 'А', '201', 2, 'Петров С.В.', 'monday'),
    (5, 'А', '305', 3, 'Сидорова О.П.', 'monday'),
    (5, 'А', '104', 1, 'Козлов А.Н.', 'tuesday'),
    (5, 'А', '201', 2, 'Иванова М.И.', 'tuesday'),
    (6, 'Б', '208', 1, 'Смирнов В.К.', 'monday'),
    (6, 'Б', '105', 2, 'Федорова Л.М.', 'monday'),
]

cursor.executemany(
    "INSERT INTO lessons (class_number, class_letter, classroom, lesson_number, teacher, day_of_week) VALUES (?, ?, ?, ?, ?, ?)",
    test_lessons
)

conn.commit()
conn.close()

print("Новая база данных создана с тестовыми данными")