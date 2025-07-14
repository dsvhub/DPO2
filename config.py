# config.py

import os
import json
from tkinter import simpledialog, messagebox, Tk

CONFIG_FILE = "email_config.json"

def prompt_email_config():
    root = Tk()
    root.withdraw()  # Hide main window

    messagebox.showinfo("Email Setup", "Please enter your email login for sending files.")
    email = simpledialog.askstring("Email", "Enter your email address:")
    password = simpledialog.askstring("Password", "Enter your email password:", show='*')

    if not email or not password:
        messagebox.showerror("Error", "Email and password are required.")
        root.destroy()
        raise Exception("Email config aborted")

    config = {
        "sender": email,
        "password": password,
        "smtp": "smtp.gmail.com",
        "port": 587
    }

    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

    root.destroy()
    return config


def get_email_config():
    if not os.path.exists(CONFIG_FILE):
        return prompt_email_config()

    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


# Load config values as variables (use lowercase keys)
config = get_email_config()

EMAIL_SENDER = config.get("sender", "")
EMAIL_PASSWORD = config.get("password", "")
SMTP_SERVER = config.get("smtp", "smtp.gmail.com")
SMTP_PORT = config.get("port", 587)

# Other static paths
RECEIPTS_FOLDER = "receipts"
CLIENT_CSV = "clients.csv"
