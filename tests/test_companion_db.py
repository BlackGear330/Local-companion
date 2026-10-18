import sys
import os
import pytest
from pathlib import Path
import sqlite3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../base')))

from companion import init_companion_db, get_companion

@pytest.fixture
def temp_db_path(tmp_path: Path) -> Path:
  """Фикстура для создания пути к временному файлу базы данных."""
  db_file = tmp_path / "test_app.db"
  return db_file


def test_create_database_and_table(temp_db_path: Path):
    # Вызыв функции создания базы
    init_companion_db(temp_db_path)
    # Проверка, что файл физически создался на диске
    assert temp_db_path.exists()

def test_tables(temp_db_path: Path):
    init_companion_db(temp_db_path)
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()
    # получаем все таблицы которые существуют в базе
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row[0] for row in cursor.fetchall()} # собираем имена таблиц в множество (set).
    # Список заложенных таблиц в архитектуре
    expected_tables = {"conversations", "messages", "memories", "memory_candidates", "settings"}
    assert expected_tables.issubset(tables), f"Не хватает таблиц. Найдено: {tables}"
    # Проверяем наличие представления active_memory
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='view';"
    )
    views = {row[0] for row in cursor.fetchall()}

    assert "active_memory" in views, (
        f"Представление active_memory не найдено. Найдено: {views}"
    )
    conn.close()

def test_active_memory(temp_db_path: Path):
    init_companion_db(temp_db_path)
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()
    cursor.execute(''' 
        INSERT INTO memories (type, content, status, certainty, source_type, created_at, updated_at)
        VALUES ('fact', 'Активный факт про зеленый чай', 'active', 'confirmed', 'manual', '2026-03-30', '2026-03-30');
    ''')
    cursor.execute(''' 
        INSERT INTO memories (type, content, status, certainty, source_type, created_at, updated_at)
        VALUES ('fact', 'Старый факт про зеленый чай', 'superseded', 'confirmed', 'manual', '2026-03-29', '2026-03-30');
    ''')
    cursor.execute(''' 
        INSERT INTO memories (type, content, status, certainty, source_type, created_at, updated_at)
        VALUES ('fact', 'Факт про кофе', 'archived', 'confirmed', 'manual', '2026-03-25', '2026-03-28');
    ''')
    conn.commit()
    cursor.execute("SELECT content FROM active_memory")
    rows = cursor.fetchall()
    conn.close()

    assert len(rows) == 1, f"Ожидалась 1 активная запись, а вернулось: {len(rows)}"
    assert rows[0][0] == 'Активный факт про зеленый чай'

def test_reinitialization (temp_db_path: Path):
    init_companion_db(temp_db_path)
    conn = sqlite3.connect(temp_db_path)
    conn.execute("INSERT INTO conversations (id, started_at, title) VALUES (1, '2026-03-30', 'Тест');")
    conn.commit()
    conn.close()

    # Вызываем инициализацию второй раз (проверяем, что ничего не стерлось)
    init_companion_db(temp_db_path)

    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT title FROM conversations WHERE id = 1;")
    title = cursor.fetchone()[0]
    conn.close()

    assert title == 'Тест'

def test_role (temp_db_path: Path):
    init_companion_db(temp_db_path)
    conn = sqlite3.connect(temp_db_path)
    # Включаем проверку внешних ключей
    conn.execute("PRAGMA foreign_keys = ON")

    # Создается разговор на который будет ссылаться тест
    conn.execute(
        "INSERT INTO conversations (id, started_at) VALUES (1, '2026-10-18')"
    )

    conn.execute(
            "INSERT INTO messages (id, conversation_id, role, content, created_at)"
            "VALUES (1, 1, 'user', 'Привет', '2026-10-18')"
    )

    conn.execute(
        "INSERT INTO messages (id, conversation_id, role, content, created_at) "
        "VALUES (2, 1, 'assistant', 'Привет!', '2026-10-18')"
    )

    conn.commit()

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO messages (id, conversation_id, role, content, created_at) "
            "VALUES (3, 1, 'bot', 'Ответ', '2026-10-18')"
        )

    conn.close()

def test_connection_enables_foreign_keys_and_wal(temp_db_path):
    init_companion_db(temp_db_path)
    conn = get_companion(temp_db_path)
    assert conn.execute('PRAGMA foreign_keys').fetchone()[0] == 1
    assert conn.execute('PRAGMA journal_mode').fetchone()[0] == 'wal'
    conn.close()

def test_required_fields(temp_db_path: Path):
    init_companion_db(temp_db_path)
    conn = sqlite3.connect(temp_db_path)
    # Создается разговор на который будет ссылаться тест
    conn.execute(
        "INSERT INTO conversations (id, started_at) VALUES (1, '2026-10-18')"
    )
    # Проверяем, что нельзя сохранить сообщение без content
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO messages "
            "(id, conversation_id, role, created_at) "
            "VALUES (1, 1, 'user', '2026-10-18')"
        )

    # Проверяем, что нельзя сохранить сообщение без conversation_id
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO messages "
            "(id, conversation_id, role, content, created_at) "
            "VALUES (2, NULL, 'user', 'Привет', '2026-10-18')"
        )

    conn.close()


def test_foreign_key(temp_db_path: Path):
    init_companion_db(temp_db_path)
    conn = sqlite3.connect(temp_db_path)
    # Включаем проверку внешних ключей
    conn.execute("PRAGMA foreign_keys = ON")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO messages (id, conversation_id, role, content, created_at) "
            "VALUES (1, 999, 'user', 'Ответ', '2026-10-18')"
        )
    conn.close()

def test_status(temp_db_path: Path):
    init_companion_db(temp_db_path)
    conn = sqlite3.connect(temp_db_path)
    # Включаем проверку внешних ключей
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(''' 
            INSERT INTO memories (type, content, status, certainty, source_type, created_at, updated_at)
            VALUES ('fact', 'Факт про кофе', 'deleted', 'confirmed', 'manual', '2026-03-25', '2026-03-28');
        ''')
    conn.close()