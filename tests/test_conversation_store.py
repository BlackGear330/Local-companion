import sys
import os
import pytest
from pathlib import Path
import sqlite3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../base')))

from companion import init_companion_db, new_dialog, get_dialog, get_active_dialogs, save_message, get_or_create_active_dialog, rename_dialog, set_dialog_status, load_messages, get_setting, set_setting

@pytest.fixture
def temp_db_path(tmp_path: Path) -> Path:
  """Фикстура для создания пути к временному файлу базы данных."""
  db_file = tmp_path / "test_app.db"
  return db_file

def test_save_and_load_messages(temp_db_path: Path):
    """Проверяем сохранение и загрузку сообщений"""
    init_companion_db(temp_db_path)
    dialog_id = new_dialog(temp_db_path)
    save_message(temp_db_path, dialog_id, "user", "test")
    test = load_messages(temp_db_path, dialog_id)
    assert test == [
    {
        "role": "user",
        "content": "test"
    }
]

def test_messages_do_not_mix_between_dialogs(temp_db_path: Path):
    init_companion_db(temp_db_path)
    dialog_id1 = new_dialog(temp_db_path)
    save_message(temp_db_path, dialog_id1, "user", "Привет")
    dialog_id2 = new_dialog(temp_db_path)
    save_message(temp_db_path, dialog_id2, "user", "Пока")
    test1 = load_messages(temp_db_path, dialog_id1)
    test2 = load_messages(temp_db_path, dialog_id2)
    assert test1 == [
    {
        "role": "user",
        "content": "Привет"
    }
] and test2 == [
    {
        "role": "user",
        "content": "Пока"
    }
]

def test_messages_order(temp_db_path: Path):
    init_companion_db(temp_db_path)
    dialog_id = new_dialog(temp_db_path)
    save_message(temp_db_path, dialog_id, "user", "test")
    save_message(temp_db_path, dialog_id, "user", "test2")
    save_message(temp_db_path, dialog_id, "user", "test3")
    test = load_messages(temp_db_path, dialog_id)
    assert test == [
    {
        "role": "user",
        "content": "test"
    },
    {
        "role": "user",
        "content": "test2"
    },
    {
        "role": "user",
        "content": "test3"
    }
]


def test_save_message_updates_last_message_at(temp_db_path: Path):
    init_companion_db(temp_db_path)
    dialog_id = new_dialog(temp_db_path)
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT last_message_at FROM conversations WHERE id = ?", (dialog_id,))
    last_message_at = cursor.fetchone()[0]
    assert last_message_at is None
    save_message(temp_db_path, dialog_id, "user", "test")
    cursor.execute("SELECT last_message_at FROM conversations WHERE id = ?", (dialog_id,))
    last_message_at = cursor.fetchone()[0]
    assert last_message_at is not None
    conn.close()


def test_create_main_dialog_on_empty_db(temp_db_path: Path):
    init_companion_db(temp_db_path)
    dialog_id = get_or_create_active_dialog(temp_db_path)
    dialog_info = get_dialog(temp_db_path, dialog_id)
    assert dialog_id is not None
    assert dialog_id == int(get_setting(temp_db_path, 'active_conversation_id'))
    assert dialog_info[1] == 'Основной'

def test_get_active_dialog_when_saved_is_archived(temp_db_path: Path):
    init_companion_db(temp_db_path)
    dialog_id1 = new_dialog(temp_db_path)
    set_setting(temp_db_path, 'active_conversation_id', dialog_id1)
    set_dialog_status(temp_db_path, dialog_id1, 'archived')
    new_active_id = get_or_create_active_dialog(temp_db_path)
    assert new_active_id != dialog_id1
    assert int(get_setting(temp_db_path, 'active_conversation_id')) == new_active_id
