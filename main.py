import openai
from openai import OpenAI
from pathlib import Path
from base.companion import save_message, get_or_create_active_dialog, load_messages, new_dialog, get_active_dialogs, get_dialog, set_setting, rename_dialog, set_dialog_status
from commands import handle_command
from base.utils import persona, limit_messages


print("Чат с локальной моделью запущен.  \nДля выхода введите '1' \nЧтобы узнать список команд введите '/help'")

client = OpenAI(
    base_url = 'http://127.0.0.1:1234/v1',
    api_key = 'LM',
)


ai_persona = persona()



base_dir = Path(__file__).resolve().parent
db_path = base_dir / 'base' / 'companion.db'
dialog_id = get_or_create_active_dialog(db_path)



while True:
    user_message = input("\nВы: ").strip()
    if not user_message:
        continue
    if user_message.startswith('//'):
        user_message = user_message[1:]
    elif user_message.startswith('/'):
        dialog_id = handle_command(user_message, db_path, dialog_id)
        continue
    if user_message == '1':
        print("\nСессия завершена.")
        break
    save_message(db_path, dialog_id, "user", user_message)
    full_history = load_messages(db_path, dialog_id)
    limited_history = limit_messages(full_history, limit=30)
    current_context = [{"role": "system", "content": ai_persona}] + limited_history

    try:
        response = client.chat.completions.create(
            model= 'qwen/qwen3.5-9b',
            messages = current_context,
            temperature = 0.8
        )
    except openai.OpenAIError as e:
        print(f"\nОшибка модели: {e}. Попробуйте отправить сообщение еще раз.")
        continue

    output_model = response.choices[0].message.content
    save_message(db_path, dialog_id, "assistant", output_model)
    print("\nОтвет модели:",output_model)