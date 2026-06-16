import json
import os

CONFIG_FILE = 'winfix.json'

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.loads(f.read())
        except Exception:
            return {"version": "2.0", "last_run": ""}
    
    return {"version": "2.0", "last_run": "", "logs": []}