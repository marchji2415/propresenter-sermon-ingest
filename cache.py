import os, json

def make_cache_root(script_dir):
    root = os.path.join(script_dir, "cache")
    os.makedirs(os.path.join(root, "bible"), exist_ok=True)
    os.makedirs(os.path.join(root, "ai"), exist_ok=True)
    return root

def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
