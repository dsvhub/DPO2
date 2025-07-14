# main.py

import ttkbootstrap as ttk
from utils import ensure_dir, is_email_config_missing
from config import RECEIPTS_FOLDER
from login import show_login
from gui import DPOApp  # Don't forget this

if __name__ == "__main__":
    ensure_dir("assets/files")
    ensure_dir(RECEIPTS_FOLDER)

    # Step 1: Login window
    login_success = show_login()

    if login_success:
        # Step 2: Launch main app only after successful login
        root = ttk.Window(themename="cosmo")
        root.title("Digital Product Organizer")

        dpo = DPOApp(root)

        if is_email_config_missing():
            dpo.open_email_settings()

        root.mainloop()
