from openai import OpenAI
from pathlib import Path


print("Чат с локальной моделью запущен. Для выхода введите '1'.")

client = OpenAI(
    base_url = 'http://127.0.0.1:1234/v1',
    api_key = 'LM',
)
def persona():
    base_dir = Path(__file__).resolve().parent
    file_path = base_dir / 'settings' / 'persona.txt'
    with open(file_path, 'r', encoding= 'utf-8') as f:
        content = f.read()
    return content

ai_persona = persona()

messages= [
    {"role": "system", "content": ai_persona},
]

while True:
    user_message = input("\nВы: ").strip()
    if user_message == '1':
        print("Сессия завершена.")
        break
    messages.append({"role": "user", "content": user_message})
    response = client.chat.completions.create(
    model= 'qwen/qwen3.5-9b',
    messages = messages,
    temperature = 0.2
)
    messages.append({"role": "assistant", "content": response.choices[0].message.content})
    print(response.choices[0].message.content)