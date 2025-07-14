# setup.py
import sys
from cx_Freeze import setup, Executable

# Build options
build_exe_options = {
"packages": [
    "os", "tkinter", "csv", "smtplib", "email", "shutil", "ttkbootstrap", "reportlab", "fpdf",
    "datetime"
],
"includes": [
    "fpdf"
    ],
    "include_files": [
        ("assets", "assets"),
        ("templates", "templates"),
        ("clients.csv", "clients.csv"),
        "config.py",
        "logger.py",
        "utils.py",
        "emailer.py",
        "client_data.py",
        "receipt_generator.py"
    ],
    "includes": [
        "tkinter", "tkinter.ttk", "tkinter.messagebox", "tkinter.filedialog", "tkinter.simpledialog"
    ],
    "include_msvcr": True  # Ensures required Microsoft runtime DLLs are included
}

# Hide console window on Windows
base = "Win32GUI" if sys.platform == "win32" else None

setup(
    name="Digital Product Organizer",
    version="1.0",
    description="A file organizer and emailer for digital products",
    options={"build_exe": build_exe_options},
    Executables=[
        Executable("main.py", base=base, target_name="DPO.exe", icon="assets/app_icon.ico")
    ]
)
