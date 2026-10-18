import os
import sqlite3


def get_activity(db_path):
    conn = sqlite3.connect(db_path, timeout=10.0)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute('PRAGMA journal_mode=WAL;')
    return conn

def init_activity_db(db_path):
    conn = get_activity(db_path)
    try:
        cur = conn.cursor()

        # таблица событий активности
        cur.execute ('''
        CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY,         -- Идентификатор
        process_name TEXT NOT NULL,     -- Имя программы
        window_title TEXT,              -- Заголовок окна (по умолчанию не записывается)
        started_at TEXT NOT NULL,       -- Время начала.
        ended_at TEXT,                  -- Время окончания (пусто, пока событие идёт)
        processed_at TEXT               -- Время когда мозг обработал событие (пусто, если ещё нет)
        )
        ''')

        # таблица сохранённых кадров
        cur.execute ('''
        CREATE TABLE IF NOT EXISTS frames(
        id INTEGER PRIMARY KEY,                                                                     -- Идентификатор
        event_id INTEGER REFERENCES events (id) ON DELETE SET NULL,                                 -- К какому событию относится
        path TEXT NOT NULL,                                                                         -- Путь к файлу изображения
        captured_at TEXT NOT NULL,                                                                  -- Время когда снят
        trigger TEXT NOT NULL CHECK (trigger IN('change', 'sound', 'window', 'text', 'hotkey')),    -- Что вызвало сохранение
        ocr_text TEXT,                                                                              -- Прочитанный текст
        processed_at TEXT,                                                                          -- Время когда разобран
        deleted_at TEXT                                                                             -- Время когда файл изображения удален
        )
        ''')
        conn.commit()
    finally:
        conn.close()

if __name__ == "__main__":
    db_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(db_dir, "activity.db")
    init_activity_db(db_path)