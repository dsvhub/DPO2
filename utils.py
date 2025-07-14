import json
import os

EMAIL_CONFIG_PATH = "email_config.json"

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def validate_client_inputs(name, files):
    return bool(name.strip()) and bool(files)

def is_email_config_missing():
    if not os.path.exists(EMAIL_CONFIG_PATH):
        return True
    try:
        with open(EMAIL_CONFIG_PATH, "r") as f:
            data = json.load(f)
        return not data.get("sender") or not data.get("password")
    except Exception:
        return True

def load_email_config():
    if not os.path.exists(EMAIL_CONFIG_PATH):
        return {"sender": "", "password": ""}
    try:
        with open(EMAIL_CONFIG_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {"sender": "", "password": ""}

def save_email_config(sender, password):
    data = {
        "sender": sender,
        "password": password
    }
    with open(EMAIL_CONFIG_PATH, "w") as f:
        json.dump(data, f)
