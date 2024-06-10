import os
import json

def save_settings(cfg):
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=4)

def load_settings():
    with open('default_config.json', 'r', encoding='utf-8') as f:
        default_config = json.load(f)

    if os.path.exists('config.json'):
        with open('config.json', 'r', encoding='utf-8') as f:
            cfg = json.load(f)
    else:
        cfg = {}

    for k, v in default_config.items():
        cfg.setdefault(k, v)

    return cfg

cfg = load_settings()
