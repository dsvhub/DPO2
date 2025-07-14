# client_data.py
import csv
import os
from config import CLIENT_CSV
import csv
from datetime import datetime


def save_client_info(name, email, files):
    os.makedirs("assets/client", exist_ok=True)
    filepath = "clients.csv"

    file_str = "|".join(files)
    now = datetime.now().strftime('%Y-%m-%d %H:%M')

    file_is_new = not os.path.exists(filepath) or os.path.getsize(filepath) == 0

    with open(filepath, "a", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["name", "email", "date", "files"])
        if file_is_new:
            writer.writeheader()
        writer.writerow({
            "name": name,
            "email": email,
            "date": now,
            "files": file_str
        })

def load_clients():
    if not os.path.exists(CLIENT_CSV):
        return []
    with open(CLIENT_CSV, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header
        return list(reader)
