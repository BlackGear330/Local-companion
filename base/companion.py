import os
import sqlite3
from datetime import datetime

def get_companion(db_path):
    """Открывает соединение с БД и включает необходимые настройки SQLite."""
    conn = sqlite3.connect(db_path, timeout=10.0)
    conn.execute("PRAGMA foreign_keys = ON")  # Включаем проверку всех внешних ключей в текущем соединении.
    conn.execute('PRAGMA journal_mode=WAL;')
    return conn

def init_companion_db(db_path: str):
    """Создаёт таблицы и представление БД, если они ещё не существуют."""
    conn = get_companion(db_path)
    try:
        cur = conn.cursor()

        # таблица диалогов
        cur.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id              INTEGER PRIMARY KEY,                                   -- Идентификатор диалога
            started_at      TEXT NOT NULL,                                         -- Когда начат
            title           TEXT NOT NULL DEFAULT 'Новый диалог',                  -- Название диалога
            status          TEXT NOT NULL DEFAULT 'active'                         -- active — можно продолжать, archived — скрыт из активных
                            CHECK (status IN ('active', 'archived')),
            last_message_at TEXT                                                   -- Время последнего сообщения (обновляется при save_message)
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


def new_dialog(db_path, title: str = 'Новый диалог' ):
    """Создаёт новый диалог и возвращает его ID."""
    conn = get_companion(db_path)
    try:
        cursor = conn.cursor()
        now = datetime.now().isoformat(sep=" ", timespec="seconds")
        cursor.execute('''
        INSERT INTO conversations (started_at, title)
        VALUES (?,?)
        ''', (now, title))
        last_id = cursor.lastrowid
        conn.commit()
        return last_id
    finally:
        conn.close()

def get_dialog (db_path, dialog_id):
    """Возвращает ID, название и статус диалога или None, если он не найден."""
    conn = get_companion(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute('''
        SELECT id, title, status FROM conversations WHERE id = ?
        ''', (dialog_id,))
        result = cursor.fetchone()
        return result if result else None
    finally:
        conn.close()

def get_active_dialogs(db_path, status = 'active'):
    """Возвращает список незархивированных диалогов, начиная с недавно обновлённых."""
    conn = get_companion(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute('''
        SELECT id, title, status, last_message_at FROM conversations WHERE status = ? ORDER BY last_message_at DESC
        ''', (status,))
        result = cursor.fetchall()
        return result
    finally:
        conn.close()


def save_message(db_path, dialog_id,  role, content):
    """Сохраняет сообщение и обновляет время последнего сообщения в диалоге."""
    conn = get_companion(db_path)
    try:
        cursor = conn.cursor()
        now = datetime.now().isoformat(sep=" ", timespec="seconds")
        cursor.execute('''
        INSERT INTO messages (conversation_id, role, content, created_at)
        VALUES (?,?,?,?) 
        ''', (dialog_id, role, content, now))
        cursor.execute('''
        UPDATE conversations SET last_message_at = ?  WHERE id = ?
        ''', (now, dialog_id))
        conn.commit()
    finally:
        conn.close()

def get_or_create_active_dialog(db_path):
    """Восстанавливает активный диалог из настроек или выбирает/создаёт другой."""
    active_id = get_setting(db_path, 'active_conversation_id')
    if active_id is not None:
        dialog_info = get_dialog(db_path, active_id)
        if dialog_info is not None and dialog_info[2] == 'active':
            return int(active_id)
    dialog_info_active = get_active_dialogs(db_path)
    if dialog_info_active:
        result_dialog_info = dialog_info_active[0]
        result_dialog_id = result_dialog_info[0]
        set_setting(db_path, 'active_conversation_id', result_dialog_id)
        return result_dialog_id
    else:
        result_dialog_id = new_dialog(db_path, title='Основной')
        set_setting(db_path, 'active_conversation_id', result_dialog_id)
        return result_dialog_id

def rename_dialog(db_path, dialog_id, title):
    """Переименовывает диалог"""
    conn = get_companion(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute('''
        UPDATE conversations SET title = ? WHERE id = ?
        ''', (title, dialog_id))
        conn.commit()
    finally:
        conn.close()

def set_dialog_status(db_path, dialog_id, status):
    conn = get_companion(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute('''
        UPDATE conversations SET status = ? WHERE id = ?
        ''', (status, dialog_id))
        conn.commit()
    finally:
        conn.close()

def load_messages(db_path, dialog_id):
    """Загружает всю историю диалога в хронологическом порядке."""
    conn = get_companion(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute('''
        Select role, content FROM messages WHERE conversation_id = ? ORDER BY id ASC
        ''', (dialog_id,))
        messages = []
        result = cursor.fetchall()
        for row in result:
            message = {"role": row[0], "content": row[1]}
            messages.append(message)
        return messages
    finally:
        conn.close()

def get_setting(db_path, key):
    """Возвращает значение настройки по ключу или None, если её нет."""
    conn = get_companion(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute('''
        select value from settings where key = ?
        ''', (key,))
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        conn.close()

def set_setting(db_path, key, value):
    """Создаёт настройку или обновляет её существующее значение."""
    conn = get_companion(db_path)
    try:
        cursor = conn.cursor()
        now = datetime.now().isoformat(sep=" ", timespec="seconds")
        cursor.execute('''
        INSERT INTO settings (key, value, updated_at) VALUES (?,?,?) ON CONFLICT (key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
        ''', (key, value, now))
        conn.commit()
    finally:
        conn.close()



if __name__ == "__main__":
    db_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(db_dir, "companion.db")
    init_companion_db(db_path)