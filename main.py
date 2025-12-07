from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional
import sqlite3
import os

app = FastAPI()

# Добавляем CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Монтируем статические файлы
app.mount("/static", StaticFiles(directory="."), name="static")


class LessonCreate(BaseModel):
    class_number: int
    class_letter: str
    classroom: str
    lesson_number: int
    teacher: str
    day_of_week: str


class LessonUpdate(BaseModel):
    classroom: Optional[str] = None
    teacher: Optional[str] = None


def init_db():
    conn = sqlite3.connect('school.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lessons (
            class_number INTEGER NOT NULL,
            class_letter TEXT NOT NULL,
            lesson_number INTEGER NOT NULL,
            day_of_week TEXT NOT NULL,
            classroom TEXT NOT NULL,
            teacher TEXT NOT NULL,
            PRIMARY KEY (class_number, class_letter, lesson_number, day_of_week)
        )
    ''')
    conn.commit()
    conn.close()


init_db()


# Главная страница
@app.get("/")
async def read_root():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return {"message": "School Lessons API"}


@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Server is running"}


@app.post("/lessons/")
def create_lesson(lesson: LessonCreate):
    # Валидация дня недели
    valid_days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
    if lesson.day_of_week.lower() not in valid_days:
        raise HTTPException(status_code=400, detail="Invalid day of week")

    conn = sqlite3.connect('school.db')
    cursor = conn.cursor()

    try:
        cursor.execute(
            """INSERT INTO lessons 
               (class_number, class_letter, classroom, lesson_number, teacher, day_of_week) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (lesson.class_number, lesson.class_letter.upper(), lesson.classroom,
             lesson.lesson_number, lesson.teacher, lesson.day_of_week.lower())
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(
            status_code=409,
            detail="Lesson already exists for this class, lesson number and day"
        )
    conn.close()

    return {
        "class_number": lesson.class_number,
        "class_letter": lesson.class_letter.upper(),
        "classroom": lesson.classroom,
        "lesson_number": lesson.lesson_number,
        "teacher": lesson.teacher,
        "day_of_week": lesson.day_of_week.lower()
    }


@app.get("/lessons/class/{class_number}/{class_letter}")
def get_lessons_by_class(class_number: int, class_letter: str):
    conn = sqlite3.connect('school.db')
    cursor = conn.cursor()
    cursor.execute(
        """SELECT * FROM lessons 
           WHERE class_number=? AND class_letter=? 
           ORDER BY day_of_week, lesson_number""",
        (class_number, class_letter.upper())
    )
    lessons = cursor.fetchall()
    conn.close()

    result = []
    for lesson in lessons:
        result.append({
            "class_number": lesson[0],
            "class_letter": lesson[1],
            "lesson_number": lesson[2],
            "day_of_week": lesson[3],
            "classroom": lesson[4],
            "teacher": lesson[5]
        })

    # ВСЕГДА возвращаем массив, даже если пустой
    return result


@app.get("/lessons/class/{class_number}/{class_letter}/day/{day_of_week}")
def get_lessons_by_class_and_day(class_number: int, class_letter: str, day_of_week: str):
    conn = sqlite3.connect('school.db')
    cursor = conn.cursor()
    cursor.execute(
        """SELECT * FROM lessons 
           WHERE class_number=? AND class_letter=? AND day_of_week=?
           ORDER BY lesson_number""",
        (class_number, class_letter.upper(), day_of_week.lower())
    )
    lessons = cursor.fetchall()
    conn.close()

    result = []
    for lesson in lessons:
        result.append({
            "class_number": lesson[0],
            "class_letter": lesson[1],
            "lesson_number": lesson[2],
            "day_of_week": lesson[3],
            "classroom": lesson[4],
            "teacher": lesson[5]
        })

    return result


@app.put("/lessons/class/{class_number}/{class_letter}/lesson/{lesson_number}/day/{day_of_week}")
def update_lesson(class_number: int, class_letter: str, lesson_number: int, day_of_week: str,
                  lesson_update: LessonUpdate):
    conn = sqlite3.connect('school.db')
    cursor = conn.cursor()

    # Проверяем существование урока
    cursor.execute(
        """SELECT * FROM lessons 
           WHERE class_number=? AND class_letter=? AND lesson_number=? AND day_of_week=?""",
        (class_number, class_letter.upper(), lesson_number, day_of_week.lower())
    )
    lesson = cursor.fetchone()
    if lesson is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Lesson not found")

    # Обновляем только разрешенные поля
    update_fields = []
    update_values = []

    if lesson_update.classroom is not None:
        update_fields.append("classroom = ?")
        update_values.append(lesson_update.classroom)

    if lesson_update.teacher is not None:
        update_fields.append("teacher = ?")
        update_values.append(lesson_update.teacher)

    if update_fields:
        update_values.extend([class_number, class_letter.upper(), lesson_number, day_of_week.lower()])
        query = f"""UPDATE lessons SET {', '.join(update_fields)} 
                    WHERE class_number=? AND class_letter=? AND lesson_number=? AND day_of_week=?"""
        cursor.execute(query, update_values)
        conn.commit()

    conn.close()
    return {"message": "Lesson updated successfully", "lesson_number": lesson_number}


@app.delete("/lessons/class/{class_number}/{class_letter}/lesson/{lesson_number}/day/{day_of_week}")
def delete_lesson(class_number: int, class_letter: str, lesson_number: int, day_of_week: str):
    conn = sqlite3.connect('school.db')
    cursor = conn.cursor()

    cursor.execute(
        """SELECT * FROM lessons 
           WHERE class_number=? AND class_letter=? AND lesson_number=? AND day_of_week=?""",
        (class_number, class_letter.upper(), lesson_number, day_of_week.lower())
    )
    if cursor.fetchone() is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Lesson not found")

    cursor.execute(
        """DELETE FROM lessons 
           WHERE class_number=? AND class_letter=? AND lesson_number=? AND day_of_week=?""",
        (class_number, class_letter.upper(), lesson_number, day_of_week.lower())
    )
    conn.commit()
    conn.close()
    return {"message": "Lesson deleted successfully"}


# Эндпоинт для получения всех уроков (для отладки)
@app.get("/lessons/all")
def get_all_lessons():
    conn = sqlite3.connect('school.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM lessons ORDER BY class_number, class_letter, day_of_week, lesson_number")
    lessons = cursor.fetchall()
    conn.close()

    result = []
    for lesson in lessons:
        result.append({
            "class_number": lesson[0],
            "class_letter": lesson[1],
            "lesson_number": lesson[2],
            "day_of_week": lesson[3],
            "classroom": lesson[4],
            "teacher": lesson[5]
        })
    return result


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)