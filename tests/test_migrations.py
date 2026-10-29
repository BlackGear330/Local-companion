import sys
import os
import pytest
from pathlib import Path
import sqlite3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../base')))

from companion import init_companion_db

@pytest.fixture
def temp_db_path(tmp_path: Path) -> Path:
  """Фикстура для создания пути к временному файлу базы данных."""
  db_file = tmp_path / "test_app.db"
  return db_file

def test_migration_adds_columns(temp_db_path: Path):
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()
    cursor.execute('PRAGMA foreign_keys = ON')
    cursor.execute('''CREATE TABLE conversations (
    id INTEGER PRIMARY KEY,
    started_at TEXT NOT NULL,
    title TEXT
)''')
    cursor.execute('''INSERT INTO conversations (id, started_at, title) VALUES (1, '2026-01-01', 'Старый диалог');''')
    conn.commit()
    conn.close()
    init_companion_db(temp_db_path)
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT title, status FROM conversations WHERE id = 1")
    result = cursor.fetchone()
    assert result[0] == 'Старый диалог'
    assert result[1] == 'active'