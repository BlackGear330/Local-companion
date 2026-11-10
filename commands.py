from base.companion import new_dialog, get_active_dialogs, get_dialog, set_setting, rename_dialog, set_dialog_status

def handle_command(user_message, db_path, dialog_id):
    """Обрабатывает команды. Возвращает актуальный dialog_id."""
    parts = user_message.split()
    command_user = parts[0]
    if command_user == '/help':
        print(
            "\nДоступные команды для вызова: \n'/new' - начать новый диалог, \n'/list' - увидеть список диалогов и когда было написано последнее сообщение, \n'/open' - переключиться на выбранный по id диалог, \n'/rename' - переименовать диалог, не меняя активный, \n'/archive' - архивирвоать диалог, \n'/unarchive' - вернуть архивный диалог в активные, \nЧтобы отправить сообщение, начинающееся со слэша, используйте // (например, //ls)")
    elif command_user == '/new':
        dialog_id = new_dialog(db_path)
        set_setting(db_path, 'active_conversation_id', dialog_id)
        print(f'\nНачат новый диалог. ID: {dialog_id}, название: "Новый диалог"')
    elif command_user == '/list':
        active_dialogs = get_active_dialogs(db_path, status='active')
        print("\n--- Список диалогов ---")
        print("\n")
        for dialog in active_dialogs:
            last_msg = dialog[3] if dialog[3] is not None else "нет сообщений"
            if dialog[0] == dialog_id:
                print(f"-> ID: {dialog[0]} (ТЕКУЩИЙ) | Название: {dialog[1]} | Последнее: {last_msg}")
                print("-----------------------")
            else:
                print(f"   ID: {dialog[0]} | Название: {dialog[1]} | Последнее: {last_msg}")
                print("-----------------------")
        archived_dialogs = get_active_dialogs(db_path, status='archived')
        if archived_dialogs:
            print("\n--- АРХИВНЫЕ ДИАЛОГИ ---")
            for dialog in archived_dialogs:
                last_msg = dialog[3] if dialog[3] is not None else "нет сообщений"
                print(f"   ID: {dialog[0]} | Название: {dialog[1]} | Последнее: {last_msg}")
                print("-----------------------")
    elif command_user == '/open':
        if len(parts) < 2:
            print("\nОшибка: укажите ID диалога. Пример: /open 3")
            return dialog_id
        try:
            new_dialog_id = int(parts[1])
        except ValueError:
            print("\nОшибка: ID должен быть числом.")
            return dialog_id
        dialog_info = get_dialog(db_path, new_dialog_id)
        if dialog_info is None:
            print(f"\nОшибка: Диалог с ID {new_dialog_id} не найден.")
        elif dialog_info[2] == 'archived':
            print(f"\nОшибка: Диалог с ID {new_dialog_id} находится в архиве.")
        else:
            dialog_id = new_dialog_id
            set_setting(db_path, 'active_conversation_id', dialog_id)
            print(f"\nОткрыт диалог: {dialog_info[1]} (ID: {dialog_id})")
    elif command_user == '/rename':
        if len(parts) < 3:
            print('Ошибка: укажите ID и новое название. Пример: /rename 3 Проект Х')
            return dialog_id
        if not parts[1].isdigit():
            print('Ошибка: ID должен быть числом.')
            return dialog_id
        target_dialog_id = int(parts[1])
        new_name = " ".join(parts[2:])

        dialog_info = get_dialog(db_path, target_dialog_id)
        if dialog_info is None:
            print(f'Ошибка: Диалог с ID {target_dialog_id} не найден.')
            return dialog_id
        rename_dialog(db_path, target_dialog_id, new_name)
        print(f'Диалог {target_dialog_id} успешно переименован в "{new_name}"')
    elif command_user == '/archive':
        if len(parts) >= 2 and parts[1].isdigit():
            target_dialog_id = int(parts[1])
            if get_dialog(db_path, target_dialog_id) is None:
                print("Диалог не найден")
                return dialog_id
            set_dialog_status(db_path, target_dialog_id, 'archived')
            if target_dialog_id == dialog_id:
                available_dialogs = get_active_dialogs(db_path)
                if len(available_dialogs) > 0:
                    dialog_id = available_dialogs[0][0]
                    set_setting(db_path, 'active_conversation_id', dialog_id)
                    print(f"Текущий диалог заархивирован. Переключился на: {dialog_id}")
                else:
                    dialog_id = new_dialog(db_path)
                    set_setting(db_path, 'active_conversation_id', dialog_id)
                    print(f"Все диалоги в архиве. Создан новый: {dialog_id}")
            else:
                print(f"Диалог {target_dialog_id} заархивирован.")
        else:
            print("Введите корректную команду: /archive <id>")
            return dialog_id
    elif command_user == '/unarchive':
        if len(parts) >= 2 and parts[1].isdigit():
            target_dialog_id = int(parts[1])
            dialog_info = get_dialog(db_path, target_dialog_id)
            if dialog_info is None:
                print("Диалог не найден")
                return dialog_id
            elif dialog_info[2] != 'archived':
                print("Этот диалог не находится в архиве.")
                return dialog_id
            set_dialog_status(db_path, target_dialog_id, 'active')
            print(f"Диалог {target_dialog_id} разархивирован")
        else:
            print("Ошибка: укажите ID диалога. Пример: /unarchive 3")
            return dialog_id
    else:
        print("Неизвестная команда. Введите /help")
    return dialog_id

