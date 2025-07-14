# auth.py
import csv
import bcrypt
import os

USER_FILE = "users.csv"

def create_user(username, password):
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    file_exists = os.path.exists(USER_FILE)
    with open(USER_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["username", "password"])
        if not file_exists or os.path.getsize(USER_FILE) == 0:
            writer.writeheader()
        writer.writerow({"username": username, "password": hashed})

def authenticate_user(username, password):
    if not os.path.exists(USER_FILE):
        return False
    with open(USER_FILE, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["username"] == username and bcrypt.checkpw(password.encode(), row["password"].encode()):
                return True
    return False
