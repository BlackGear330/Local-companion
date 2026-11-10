import json
import openai
from openai import OpenAI
from utils import prompt_memory


client = OpenAI(
    base_url = 'http://127.0.0.1:1234/v1',
    api_key = 'LM',
)

ai_promt = prompt_memory()



def llm_examples():
    with open("./tests/data/memory_examples.json", "r", encoding='utf-8') as file:
        data = json.load(file)
    """dev_examples использовался для настройки"""
    dev_examples = data["development"]
    test_examples = data["test"]
    correct = 0
    total = len(test_examples)
    for example in test_examples:
        text = example["text"]
        expected = example["expected_result"]
        actual = [{"role": "system", "content": ai_promt},
                    {"role": "user", "content": text},]
        try:
            response = client.chat.completions.create(
                model='qwen/qwen3.5-9b',
                messages=actual,
                temperature=0.1
            )
        except openai.OpenAIError as e:
            print(f"\nОшибка модели: {e}.")
            continue
        try:
            output_model = response.choices[0].message.content
            clean_text = output_model.strip().replace("```json", "").replace("```", "")
            actual_result = json.loads(clean_text)
            print(f"\n--- Текст: {text} ---")
            print(f"Ожидалось: {expected}")
            print(f"Ответ модели: {actual_result}")
            if expected is None:
                if len(actual_result) == 0:
                    correct += 1
                    print("[УСПЕХ]")
                else:
                    print("[ОШИБКА] Модель выдумала факт")
            else:
                if len(actual_result) == 0:
                    print("[ОШИБКА] Пропуск")
                    continue
                else:
                    if any(item["type"] == expected["type"] for item in actual_result):
                        correct += 1
                        print("[УСПЕХ]")
                    else:
                        print("[ОШИБКА] Неверный тип")
            for item in actual_result:
                quote = item["source_quote"]
                if quote not in text:
                    print(f"[ОШИБКА] Галлюцинация! Цитаты '{quote}' нет в тексте.")
            print(f"Итого: {correct} из {total}")

        except json.JSONDecodeError as e:
            print("json.JSONDecodeError")

llm_examples()



