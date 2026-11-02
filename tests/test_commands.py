from base.utils import limit_messages
from commands import handle_command
import pytest
from pathlib import Path
from base.companion import init_companion_db, get_setting, get_dialog, new_dialog, get_or_create_active_dialog


@pytest.fixture
def temp_db_path(tmp_path: Path) -> Path:
    db_file = tmp_path / "test_app.db"
    return db_file


def test_limit_messages():
    lim = list(range(1, 41))
    limited_history = limit_messages(lim, limit=30)
    assert len(limited_history) == 30
    assert limited_history[0] == 11

def test_new_command(temp_db_path: Path):
    init_companion_db(temp_db_path)
    old_id = get_or_create_active_dialog(temp_db_path)
    new_id = handle_command('/new', temp_db_path, old_id)
    assert new_id != old_id
    assert int(get_setting(temp_db_path, 'active_conversation_id')) ==new_id

def test_rename_command(temp_db_path: Path):
    init_companion_db(temp_db_path)
    current_id = get_or_create_active_dialog(temp_db_path)
    new_name = handle_command(f'/rename {current_id} Проект_Альфа', temp_db_path, current_id)
    assert new_name == current_id
    assert get_dialog(temp_db_path, current_id)[1] == "Проект_Альфа"

def test_archive_command(temp_db_path: Path):
    init_companion_db(temp_db_path)
    current_id = get_or_create_active_dialog(temp_db_path)
    archived = handle_command(f'/archive {current_id}', temp_db_path, current_id)
    assert archived != current_id
    assert get_dialog(temp_db_path, current_id)[2] == 'archived'
    assert int(get_setting(temp_db_path, 'active_conversation_id')) == archived

def test_invalid_command(temp_db_path):
    init_companion_db(temp_db_path)
    current_id = get_or_create_active_dialog(temp_db_path)
    invalid_name = handle_command('/rename abc Проект_Альфа', temp_db_path, current_id)
    assert invalid_name == current_id
    assert get_dialog(temp_db_path, current_id)[1] == "Основной"
