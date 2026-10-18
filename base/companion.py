import os
import sqlite3


def get_companion(db_path):
    conn = sqlite3.connect(db_path, timeout=10.0)
    conn.execute("PRAGMA foreign_keys = ON")  # Включаем проверку всех внешних ключей в текущем соединении.
    conn.execute('PRAGMA journal_mode=WAL;')
    return conn

def init_companion_db(db_path: str):
    conn = get_companion(db_path)
    try:
        cur = conn.cursor()

        # таблица диалогов
        cur.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY,                         -- Идентификатор диалога
            started_at TEXT NOT NULL,                       -- Когда начат
            title TEXT                                      -- Название диалога
        )
        ''')

        # таблица сообщений
        cur.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY,                                             -- Идентификатор
            conversation_id INTEGER NOT NULL REFERENCES conversations (id),     -- К какому диалогу относится     
            role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),           -- Кто написал   
            content TEXT NOT NULL,                                              -- Текст сообщения
            created_at TEXT NOT NULL                                            -- Время когда написано сообщение
        )
        ''')

        # таблица памяти
        cur.execute('''
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY,                                                                                 -- Идентификатор
            type TEXT NOT NULL CHECK (type IN ('fact', 'preference', 'goal', 'project', 
                                                'game', 'observation', 'inference')),                               -- Вид записи
            content TEXT NOT NULL,                                                                                  -- Формулировка
            status TEXT NOT NULL CHECK (status IN ('active', 'superseded', 'archived')),                            -- active используется, superseded заменена новой версией, archived в архиве
            certainty TEXT NOT NULL CHECK (certainty IN ('confirmed', 'assumed')),                                  -- Подтверждено или предположение
            source_type TEXT NOT NULL CHECK (source_type IN ('message', 'manual', 'activity', 'screen', 'brain')),  -- Откуда запись
            source_id INTEGER,                                                                                      -- Номер исходного объекта                                                                                       
            source_quote TEXT,                                                                                      -- Цитата из источника
            source_time TEXT,                                                                                       -- Когда произошло исходное событие
            replaces_id INTEGER REFERENCES memories (id),                                                           -- Номер записи, которую эта заменила (цепочка версий)
            expires_at TEXT,                                                                                        -- Срок актуальности для временных записей
            created_at TEXT NOT NULL,                                                                               -- Когда создана
            updated_at TEXT NOT NULL                                                                                -- Когда изменена
        )
        ''')

        # представление: только активные записи памяти
        cur.execute('''
        CREATE VIEW IF NOT EXISTS active_memory AS
        SELECT * FROM memories WHERE status = 'active'
        ''')

        # таблица кандадитов в память
        cur.execute('''
        CREATE TABLE IF NOT EXISTS memory_candidates (
            id INTEGER PRIMARY KEY,                                                         -- Идентификатор
            content TEXT NOT NULL,                                                          -- Предложенная формулировка
            type TEXT NOT NULL CHECK (type IN ('fact', 'preference', 'goal', 'project',     -- Предложенный вид
                                                'game', 'observation', 'inference')),                                                 
            certainty TEXT NOT NULL CHECK (certainty IN ('confirmed', 'assumed')),          -- confirmed или assumed
            source_type TEXT NOT NULL CHECK (source_type IN ('message', 'manual', 'activity',
                                                             'screen', 'brain')),           -- Источник обязателен и ограничен допустимыми значениями   
            source_id INTEGER,                                                              -- Номер исходного объекта
            source_quote TEXT,                                                              -- Цитата из источника, которую проверяет код
            source_time TEXT,                                                               -- Когда произошло исходное событие
            status TEXT NOT NULL CHECK (status IN ('pending', 
                                        'accepted', 'rejected')),                           -- Ожидает, принято, отклонено
            decision_reason TEXT CHECK (decision_reason IN ('not_important', 
                                        'wrong', 'private', 'other')),                      -- Причина отказа
            edited_content TEXT,                                                            -- Формулировка, которую поправил пользователь
            memory_id INTEGER REFERENCES memories (id),                                     -- Номер созданной записи памяти, если принято
            created_at TEXT NOT NULL,                                                       -- Когда предложено
            decided_at TEXT                                                                 -- Когда принято решение
        )
        ''')

        # таблица настроек
        cur.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,          -- Уникальное имя настройки
            value TEXT NOT NULL,           -- Значение настройки
            updated_at TEXT NOT NULL       -- Когда настройка изменена
        )
        ''')

        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    db_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(db_dir, "companion.db")
    init_companion_db(db_path)