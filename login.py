# login.py

import tkinter as tk
from tkinter import simpledialog, messagebox

def show_login():
    login_win = tk.Tk()
    login_win.withdraw()  # Hide the root

    username = simpledialog.askstring("Login", "Enter username:", parent=login_win)
    password = simpledialog.askstring("Login", "Enter password:", parent=login_win, show="*")

    if username == "" and password == "":
        return True
    else:
        messagebox.showerror("Login Failed", "Invalid username or password.")
        return False