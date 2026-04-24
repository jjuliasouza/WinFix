import json
import os

CONFIG_FILE = 'winfix.json'


def load_config():
    """
    Carrega configurações do arquivo winfix.json.

    Returns:
        dict: Configurações do app (version, last_run, logs).
    """
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                print(f"Config carregada: v{config.get('version', '1.0')}")
        except Exception:
            config = {"version": "2.0", "last_run": ""}
    else:
        config = {"version": "2.0", "last_run": "", "logs": []}
    return config
