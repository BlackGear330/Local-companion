from pathlib import Path


def persona():
    base_dir = Path(__file__).resolve().parent.parent 
    file_path = base_dir / 'settings' / 'persona.txt'
    with open(file_path, 'r', encoding= 'utf-8') as f:
        content = f.read()
    return content

def limit_messages(history, limit: int = 30):
    result = history[-limit:]
    return result