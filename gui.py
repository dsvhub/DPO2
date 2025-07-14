import os
import shutil
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap import Treeview
from tkinter import filedialog, messagebox

from emailer import send_files_with_receipt
from receipt_generator import create_pdf_receipt
from client_data import save_client_info
from utils import validate_client_inputs, ensure_dir, load_email_config, save_email_config
from logger import logger
from datetime import datetime

import csv



BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
CLIENT_CSV_PATH = os.path.join(BASE_DIR, "clients.csv")
EMAILS_CSV_PATH = os.path.join(BASE_DIR, "assets", "client", "emails.csv")
RECEIPT_FOLDER = os.path.join(BASE_DIR, "receipts")
FILES_FOLDER = os.path.join(BASE_DIR, "assets", "files")



class DPOApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Digital Product Organizer")
        self.file_paths = []

        # Variables
        self.client_name_var = ttk.StringVar()
        self.client_email_var = ttk.StringVar()
        self.price_var = ttk.StringVar()
        self.tax_var = ttk.StringVar()
        self.discount_var = ttk.StringVar()
        self.send_receipt_var = ttk.BooleanVar(value=False)

        self.template_var = ttk.StringVar()

        self.email_body_text = None  # Will be assigned later

        ensure_dir(FILES_FOLDER)
        self.build_ui()

    def build_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # Send Files tab
        self.send_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.send_tab, text="Send Files")
        self.build_send_tab(self.send_tab)

        # Saved Clients tab
        self.clients_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.clients_tab, text="Saved Clients")
        self.build_clients_tab(self.clients_tab)

        # All Files tab
        self.files_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.files_tab, text="All Files")
        self.build_files_tab(self.files_tab)

        # Client Receipts tab
        self.receipts_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.receipts_tab, text="Client Receipts")
        self.build_receipts_tab(self.receipts_tab)

    def build_send_tab(self, tab):
        frm = ttk.Frame(tab, padding=10)
        frm.pack(fill=BOTH, expand=True)

        # Client Name (dropdown from clients.csv)
        ttk.Label(frm, text="Client Name:").grid(row=0, column=0, sticky=W, padx=5, pady=2)
        self.client_name_combo = ttk.Combobox(frm, textvariable=self.client_name_var,
                                              values=self.get_client_names(),
                                              state="readonly", width=40)
        self.client_name_combo.grid(row=0, column=1, sticky=EW, padx=5, pady=2)
        self.client_name_combo.bind("<<ComboboxSelected>>", self.update_email_for_selected_name)

        # Client Email (auto updated from emails.csv)
        ttk.Label(frm, text="Client Email:").grid(row=1, column=0, sticky=W, padx=5, pady=2)
        self.client_email_combo = ttk.Combobox(frm, textvariable=self.client_email_var, values=[],
                                               state="readonly", width=40)
        self.client_email_combo.grid(row=1, column=1, sticky=EW, padx=5, pady=2)

        # Email Template
        ttk.Label(frm, text="Email Template:").grid(row=2, column=0, sticky=W, padx=5, pady=2)
        self.template_combo = ttk.Combobox(frm, textvariable=self.template_var,
                                           values=self.get_available_templates(),
                                           state="readonly", width=40)
        self.template_combo.grid(row=2, column=1, sticky=EW, padx=5, pady=2)
        self.template_combo.bind("<<ComboboxSelected>>", self.load_selected_template)

        # Email body preview / edit
        ttk.Label(frm, text="Email Body Preview / Edit:").grid(row=3, column=0, columnspan=2, sticky=W, padx=5, pady=2)
        self.email_body_text = tk.Text(frm, height=6, wrap="word")
        self.email_body_text.grid(row=4, column=0, columnspan=2, sticky=NSEW, padx=5, pady=5)

        # Price, Tax, Discount
        ttk.Label(frm, text="Price ($):").grid(row=5, column=0, sticky=W, padx=5, pady=2)
        ttk.Entry(frm, textvariable=self.price_var).grid(row=5, column=1, sticky=EW, padx=5, pady=2)

        ttk.Label(frm, text="Tax ($):").grid(row=6, column=0, sticky=W, padx=5, pady=2)
        ttk.Entry(frm, textvariable=self.tax_var).grid(row=6, column=1, sticky=EW, padx=5, pady=2)

        ttk.Label(frm, text="Discount ($):").grid(row=7, column=0, sticky=W, padx=5, pady=2)
        ttk.Entry(frm, textvariable=self.discount_var).grid(row=7, column=1, sticky=EW, padx=5, pady=2)

        # Receipt checkbox
        ttk.Checkbutton(frm, text="Send Receipt with Files", variable=self.send_receipt_var).grid(
            row=8, column=1, columnspan=2, sticky=W, padx=5, pady=5)

        # Upload & Send Buttons
        ttk.Button(frm, text="Upload Files", bootstyle=INFO, command=self.add_files_from_system).grid(
            row=9, column=0, pady=10, padx=5, sticky=W)
        ttk.Button(frm, text="Send Files", bootstyle=SUCCESS, command=self.send_all).grid(
            row=9, column=1, pady=10, padx=5, sticky=E)

        # File tree
        tree_frame = ttk.Frame(frm)
        tree_frame.grid(row=10, column=0, columnspan=2, sticky=NSEW, pady=5)

        self.file_tree = Treeview(tree_frame, columns=("filename", "size"), show="headings", height=6)
        self.file_tree.heading("filename", text="File Name")
        self.file_tree.heading("size", text="Size (KB)")
        self.file_tree.column("filename", anchor="w", width=300)
        self.file_tree.column("size", anchor="e", width=100)
        self.file_tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        frm.columnconfigure(1, weight=1)
        frm.rowconfigure(4, weight=1)
        frm.rowconfigure(10, weight=1)

        self.load_files_from_folder()
        self.template_combo['values'] = self.get_available_templates()

    def get_available_templates(self):
        templates = []
        templates_dir = "templates"
        if os.path.exists(templates_dir):
            for file in os.listdir(templates_dir):
                if file.endswith(".txt"):
                    templates.append(file)
        return templates

    def load_selected_template(self, event=None):
        template_name = self.template_var.get().strip()
        if not template_name:
            messagebox.showwarning("No Template", "Please select a valid template.")
            return

        template_path = os.path.join("templates", template_name)
        if os.path.exists(template_path):
            try:
                with open(template_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    self.email_body_text.delete("1.0", tk.END)
                    self.email_body_text.insert(tk.END, content)
            except Exception as e:
                messagebox.showerror("Template Error", f"Failed to load template:\n{e}")
        else:
            messagebox.showerror("Template Not Found", f"Could not find:\n{template_path}")

    def get_client_names(self):
        names = set()
        if os.path.exists("clients.csv"):
            with open("clients.csv", newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = row.get("name", "").strip()
                    if name:
                        names.add(name)
        return sorted(names)

    def update_email_for_selected_name(self, event=None):
        selected_name = self.client_name_var.get()
        emails = self.get_saved_emails_for_client(selected_name)
        self.client_email_combo['values'] = emails
        if emails:
            self.client_email_var.set(emails[0])  # default to first match
        else:
            self.client_email_var.set("")

    def build_receipts_tab(self, tab):
        tree_frame = ttk.Frame(tab)
        tree_frame.pack(fill=BOTH, expand=True, pady=10)

        self.receipts_tree = Treeview(tree_frame, columns=("filename", "modified"), show="headings", height=15)
        self.receipts_tree.heading("filename", text="Receipt File")
        self.receipts_tree.heading("modified", text="Modified")
        self.receipts_tree.column("filename", width=300)
        self.receipts_tree.column("modified", width=150)
        self.receipts_tree.pack(side=LEFT, fill=BOTH, expand=True)

        scrollbar = ttk.Scrollbar(tree_frame, orient=VERTICAL, command=self.receipts_tree.yview)
        self.receipts_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)

        btn_frame = ttk.Frame(tab)
        btn_frame.pack(pady=5)

        btn_frame = ttk.Frame(tab)
        btn_frame.pack(pady=5)

        ttk.Button(btn_frame, text="Refresh", command=self.refresh_receipts_tab).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Open", bootstyle=INFO, command=self.open_selected_receipt).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Delete", bootstyle=DANGER, command=self.delete_selected_receipt).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Email", bootstyle=PRIMARY, command=self.email_selected_receipt).pack(side=LEFT, padx=5)


        self.refresh_receipts_tab()

    def refresh_receipts_tab(self):
        self.receipts_tree.delete(*self.receipts_tree.get_children())
        if not os.path.exists(RECEIPT_FOLDER):
            return

        for filename in os.listdir(RECEIPT_FOLDER):
            path = os.path.join(RECEIPT_FOLDER, filename)
            if os.path.isfile(path) and filename.endswith(".pdf"):
                mod_time = datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M")
                self.receipts_tree.insert("", "end", values=(filename, mod_time))

    def open_selected_receipt(self):
        selected = self.receipts_tree.selection()
        if not selected:
            return
        filename = self.receipts_tree.item(selected[0])["values"][0]
        path = os.path.join(RECEIPT_FOLDER, filename)
        if os.path.exists(path):
            try:
                os.startfile(path)
            except Exception as e:
                logger.error(f"Failed to open receipt: {e}")
                messagebox.showerror("Error", f"Could not open receipt:\n{e}")

    def delete_selected_receipt(self):
        selected = self.receipts_tree.selection()
        if not selected:
            return
        filename = self.receipts_tree.item(selected[0])["values"][0]
        path = os.path.join(RECEIPT_FOLDER, filename)

        confirm = messagebox.askyesno("Confirm Delete", f"Delete {filename}?")
        if confirm:
            try:
                os.remove(path)
                logger.info(f"Deleted receipt: {path}")
                self.refresh_receipts_tab()
            except Exception as e:
                logger.error(f"Error deleting receipt '{path}': {e}")
                messagebox.showerror("Error", f"Could not delete receipt:\n{e}")

    def email_selected_receipt(self):
        selected = self.receipts_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a receipt to email.")
            return

        filename = self.receipts_tree.item(selected[0])["values"][0]
        receipt_path = os.path.join(RECEIPT_FOLDER, filename)
        name = filename.split("_")[0]  # Extract name from filename

        # Load saved emails
        emails = self.get_saved_emails_for_client(name)
        if not emails:
            messagebox.showwarning("No Email Found", f"No saved emails found for {name}.")
            return

        # Create email selection dialog
        email = self.ask_email_dropdown(name, emails)
        if not email:
            return

        try:
            send_files_with_receipt(email, name, [], receipt_path)
            logger.info(f"Emailed receipt {filename} to {email}")
            messagebox.showinfo("Success", f"Receipt sent to {email}")
        except Exception as e:
            logger.exception(f"Failed to send receipt: {e}")
            messagebox.showerror("Send Failed", f"Could not send receipt:\n{e}")

    def get_saved_emails_for_client(self, name):
        filepath = "assets/client/emails.csv"
        emails = []

        if os.path.exists(filepath):
            with open(filepath, newline='') as f:
                reader = csv.DictReader(f)
                emails = [row["email"] for row in reader if row.get("name", "").strip().lower() == name.lower()]

        return sorted(set(emails))

    def ask_email_dropdown(self, name, email_options):
        popup = tk.Toplevel(self.root)
        popup.title("Choose Email")
        popup.geometry("350x150")
        popup.grab_set()

        result = {"email": None}

        ttk.Label(popup, text=f"Select email for {name}:", font=("Segoe UI", 10)).pack(pady=(10, 5))
        email_var = ttk.StringVar(value=email_options[0])
        dropdown = ttk.Combobox(popup, textvariable=email_var, values=email_options, state="readonly", width=40)
        dropdown.pack(pady=5)

        def confirm():
            result["email"] = email_var.get()
            popup.destroy()

        def cancel():
            popup.destroy()

        btn_frame = ttk.Frame(popup)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Cancel", bootstyle=SECONDARY, command=cancel).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Send", bootstyle=SUCCESS, command=confirm).pack(side=LEFT, padx=5)

        popup.wait_window()
        return result["email"]

    def get_saved_emails(self):
        filepath = "assets/client/emails.csv"
        emails = []
        if os.path.exists(filepath):
            with open(filepath, newline='') as f:
                reader = csv.DictReader(f)
                emails = sorted({row["email"] for row in reader if "email" in row})
        return emails

    def add_files_from_system(self):
        selected_files = filedialog.askopenfilenames(title="Select Files")
        for original_path in selected_files:
            filename = os.path.basename(original_path)
            dest_path = os.path.join(FILES_FOLDER, filename)

            base, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(dest_path):
                dest_path = os.path.join(FILES_FOLDER, f"{base}_{counter}{ext}")
                counter += 1

            try:
                shutil.copy2(original_path, dest_path)
                logger.info(f"Added file: {dest_path}")
            except Exception as e:
                logger.error(f"Error copying file '{original_path}': {e}")
                messagebox.showerror("Copy Error", f"Could not copy {filename}:\n{e}")

        self.load_files_from_folder()

    def load_files_from_folder(self):
        self.file_tree.delete(*self.file_tree.get_children())
        for filename in os.listdir(FILES_FOLDER):
            path = os.path.join(FILES_FOLDER, filename)
            if os.path.isfile(path):
                size_kb = round(os.path.getsize(path) / 1024, 2)
                self.file_tree.insert("", "end", values=(filename, f"{size_kb} KB"))

    def send_all(self):
        name = self.client_name_var.get().strip()
        email = self.client_email_var.get().strip()
        selected_items = self.file_tree.selection()

        if not selected_items or not name or not email:
            messagebox.showerror("Missing Info", "Name, Email, and at least one file must be selected.")
            return

        selected_files = [os.path.join(FILES_FOLDER, self.file_tree.item(i)['values'][0]) for i in selected_items]

        try:
            price = float(self.price_var.get()) if self.price_var.get() else 0
            tax = float(self.tax_var.get()) if self.tax_var.get() else 0
            discount = float(self.discount_var.get()) if self.discount_var.get() else 0
        except ValueError:
            messagebox.showerror("Invalid Input", "Price, tax, and discount must be numeric.")
            return

        # Get template content if selected
        email_body = None
        selected_template = self.template_var.get()
        if selected_template:
            template_path = os.path.join("templates", selected_template)
            if os.path.exists(template_path):
                with open(template_path, "r", encoding="utf-8") as f:
                    email_body = f.read()
                    # Optional: Replace placeholders
                    email_body = email_body.replace("{name}", name)

        try:
            receipt_path = create_pdf_receipt(name, selected_files, price, tax, discount)
            logger.info(f"Receipt created: {receipt_path}")

            if self.send_receipt_var.get():
                send_files_with_receipt(email, name, selected_files, receipt_path, body=email_body)
                logger.info(f"Email with receipt sent to {email} for {name}")
            else:
                send_files_with_receipt(email, name, selected_files, None, body=email_body)
                logger.info(f"Email sent to {email} for {name} (no receipt)")

            save_client_info(name, email, selected_files)

            # Save the sent email for future use
            self.save_sent_email(name, email)

            messagebox.showinfo("Success", "Files sent successfully.")
            self.reset_form()
        except Exception as e:
            logger.exception(f"Send failed: {e}")
            messagebox.showerror("Error", str(e))

    def save_sent_email(self, name, email):
        os.makedirs("assets/client", exist_ok=True)
        filepath = "assets/client/emails.csv"
        existing = set()

        # Load existing to avoid duplicates
        if os.path.exists(filepath):
            with open(filepath, newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    existing.add((row['name'], row['email']))

        # Write header if file is new or empty
        file_is_new = not os.path.exists(filepath) or os.path.getsize(filepath) == 0

        if (name, email) not in existing:
            with open(filepath, "a", newline='') as f:
                writer = csv.DictWriter(f, fieldnames=["name", "email"])
                if file_is_new:
                    writer.writeheader()
                writer.writerow({"name": name, "email": email})

    def reset_form(self):
        self.client_name_var.set("")
        self.client_email_var.set("")
        self.price_var.set("")
        self.tax_var.set("")
        self.discount_var.set("")
        self.send_receipt_var.set(False)
        self.load_files_from_folder()
        # Refresh email combo list with new emails
        self.client_email_combo['values'] = self.get_saved_emails()

    def build_clients_tab(self, tab):
        tree_frame = ttk.Frame(tab)
        tree_frame.pack(fill=BOTH, expand=True, pady=10)

        self.client_tree = Treeview(tree_frame, columns=("name", "email", "date", "files"), show="headings", height=10)
        self.client_tree.heading("name", text="Client Name")
        self.client_tree.heading("email", text="Email")
        self.client_tree.heading("date", text="Date")
        self.client_tree.heading("files", text="Files")

        self.client_tree.column("name", width=150)
        self.client_tree.column("email", width=180)
        self.client_tree.column("date", width=100)
        self.client_tree.column("files", width=250)

        self.client_tree.pack(side=LEFT, fill=BOTH, expand=True)

        scrollbar = ttk.Scrollbar(tree_frame, orient=VERTICAL, command=self.client_tree.yview)
        self.client_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)

        ttk.Button(tab, text="Refresh", command=self.load_clients).pack(side=LEFT, padx=5)
        ttk.Button(tab, text="Resend Selected", bootstyle=SUCCESS, command=self.resend_selected).pack(side=LEFT, padx=5)

        ttk.Button(tab, text="Add Client", bootstyle=PRIMARY, command=self.open_add_client_window).pack(side=LEFT, padx=5)
        ttk.Button(tab, text="Delete Selected", bootstyle=DANGER, command=self.delete_selected_client).pack(side=LEFT, padx=5)

        ttk.Button(tab, text="Edit Selected", bootstyle=PRIMARY, command=self.edit_selected_client).pack(side=LEFT, padx=5)

        self.load_clients()

    def load_clients(self):
        self.client_tree.delete(*self.client_tree.get_children())
        if not os.path.exists("clients.csv"):
            return

        with open("clients.csv", newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get('name', "")
                email = row.get('email', "")
                date = row.get('date', "")
                files = row.get('files', "")
                self.client_tree.insert("", "end", values=(name, email, date, files))

    def resend_selected(self):
        selected = self.client_tree.selection()
        if not selected:
            return

        item = self.client_tree.item(selected[0])
        name, email, _, files_str = item['values']
        file_paths = files_str.split("|")

        try:
            receipt_path = create_pdf_receipt(name, file_paths)
            send_files_with_receipt(email, name, file_paths, receipt_path)
            messagebox.showinfo("Sent", f"Files resent to {email}")
            logger.info(f"Resent files to {email} for {name}")
        except Exception as e:
            logger.exception(f"Resend failed: {e}")
            messagebox.showerror("Error", f"Could not resend files:\n{e}")

    def ask_email(self, name):
        import tkinter.simpledialog as sd
        return sd.askstring("Enter Email", f"Enter email address to resend files for {name}:")

    def open_add_client_window(self):
        win = tk.Toplevel(self.root)
        win.title("Add New Client")

        name_var = ttk.StringVar()
        email_var = ttk.StringVar()
        files_var = ttk.StringVar()

        ttk.Label(win, text="Client Name:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        ttk.Entry(win, textvariable=name_var).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(win, text="Email:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        ttk.Entry(win, textvariable=email_var).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(win, text="Files (optional):").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        files_entry = ttk.Entry(win, textvariable=files_var, state="readonly", width=40)
        files_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        def choose_files():
            paths = filedialog.askopenfilenames(title="Select Files")
            if paths:
                files_str = "|".join(paths)
                files_var.set(files_str)

        ttk.Button(win, text="Browse", command=choose_files, bootstyle=INFO).grid(row=2, column=2, padx=5)

        def save_client():
            name = name_var.get().strip()
            email = email_var.get().strip()
            files = files_var.get().strip() or "Please select Files Later in All Files Tab"
            date = datetime.now().strftime("%Y-%m-%d")

            if not name or not email:
                messagebox.showerror("Missing Info", "Name and email are required.")
                return

            filepath = "clients.csv"
            file_exists = os.path.exists(filepath)
            with open(filepath, "a", newline='') as f:
                writer = csv.DictWriter(f, fieldnames=["name", "email", "date", "files"])
                if not file_exists or os.path.getsize(filepath) == 0:
                    writer.writeheader()
                writer.writerow({
                    "name": name,
                    "email": email,
                    "date": date,
                    "files": files
                })

            logger.info(f"Added new client: {name} ({email})")
            self.load_clients()
            win.destroy()

        ttk.Button(win, text="Save Client", command=save_client, bootstyle=SUCCESS).grid(row=3, column=0, columnspan=3,
                                                                                         pady=10)

    def edit_selected_client(self):
        selected = self.client_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a client to edit.")
            return

        item = self.client_tree.item(selected[0])
        name, email, date, files = item["values"]

        edit_win = tk.Toplevel(self.root)
        edit_win.title(f"Edit Client: {name}")

        name_var = ttk.StringVar(value=name)
        email_var = ttk.StringVar(value=email)
        files_var = ttk.StringVar(value=files)

        ttk.Label(edit_win, text="Name:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        ttk.Entry(edit_win, textvariable=name_var).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(edit_win, text="Email:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        ttk.Entry(edit_win, textvariable=email_var).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(edit_win, text="Files:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        file_entry = ttk.Entry(edit_win, textvariable=files_var, width=40, state="readonly")
        file_entry.grid(row=2, column=1, padx=5, pady=5)

        def browse_files():
            paths = filedialog.askopenfilenames(title="Select Files")
            if paths:
                files_var.set("|".join(paths))

        ttk.Button(edit_win, text="Browse", command=browse_files, bootstyle=INFO).grid(row=2, column=2, padx=5)

        def save_edits():
            new_name = name_var.get().strip()
            new_email = email_var.get().strip()
            new_files = files_var.get().strip()

            if not new_name or not new_email:
                messagebox.showerror("Invalid Data", "Name and Email are required.")
                return

            # Update CSV
            filepath = "clients.csv"
            rows = []
            with open(filepath, newline='') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            for row in rows:
                if row["name"] == name and row["email"] == email and row["date"] == date:
                    row["name"] = new_name
                    row["email"] = new_email
                    row["files"] = new_files
                    break

            with open(filepath, "w", newline='') as f:
                writer = csv.DictWriter(f, fieldnames=["name", "email", "date", "files"])
                writer.writeheader()
                writer.writerows(rows)

            logger.info(f"Updated client: {new_name}")
            self.load_clients()
            edit_win.destroy()

        ttk.Button(edit_win, text="Save Changes", bootstyle=SUCCESS, command=save_edits).grid(row=3, column=0,
                                                                                              columnspan=3, pady=10)

    def delete_selected_client(self):
        selected = self.client_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a client to delete.")
            return

        item = self.client_tree.item(selected[0])
        name, email, _, _ = item['values']

        confirm = messagebox.askyesno("Confirm Delete", f"Delete client {name} ({email})?")
        if not confirm:
            return

        filepath = "clients.csv"
        rows = []

        with open(filepath, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['name'] != name or row['email'] != email:
                    rows.append(row)

        with open(filepath, "w", newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["name", "email", "date", "files"])
            writer.writeheader()
            writer.writerows(rows)

        logger.info(f"Deleted client: {name} ({email})")
        self.load_clients()

    def build_files_tab(self, tab):
        # Search frame
        search_frame = ttk.Frame(tab)
        search_frame.pack(fill=X, pady=(10, 0), padx=10)

        ttk.Label(search_frame, text="Search:").pack(side=LEFT)
        self.search_var = ttk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=LEFT, padx=5, fill=X, expand=True)
        search_entry.bind("<KeyRelease>", lambda e: self.refresh_files_tab())

        # Treeview frame
        tree_frame = ttk.Frame(tab)
        tree_frame.pack(fill=BOTH, expand=True, pady=10)

        self.files_tree = Treeview(
            tree_frame,
            columns=("name", "size", "modified"),
            show="headings",
            height=15,
            selectmode="extended"
        )
        self.files_tree.heading("name", text="File Name")
        self.files_tree.heading("size", text="Size")
        self.files_tree.heading("modified", text="Modified")
        self.files_tree.column("name", width=300)
        self.files_tree.column("size", width=100)
        self.files_tree.column("modified", width=150)
        self.files_tree.pack(side=LEFT, fill=BOTH, expand=True)

        scrollbar = ttk.Scrollbar(tree_frame, orient=VERTICAL, command=self.files_tree.yview)
        self.files_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)

        # Button frame
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(pady=5)

        ttk.Button(btn_frame, text="Add Files", bootstyle=PRIMARY, command=self.add_files_from_system).pack(side=LEFT,
                                                                                                            padx=5)
        ttk.Button(btn_frame, text="Edit Name", bootstyle=INFO, command=self.edit_selected_file).pack(side=LEFT,
                                                                                                           padx=5)
        ttk.Button(btn_frame, text="Open", bootstyle=SECONDARY, command=self.open_selected_file).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Delete", bootstyle=DANGER, command=self.delete_selected_file).pack(side=LEFT,
                                                                                                       padx=5)
        ttk.Button(btn_frame, text="Refresh", command=self.refresh_files_tab).pack(side=LEFT, padx=5)

        self.refresh_files_tab()
###########################################

    def edit_selected_file(self):
        selected = self.files_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a file to edit.")
            return

        item = self.files_tree.item(selected[0])
        old_name = item["values"][0]
        old_path = os.path.join(FILES_FOLDER, old_name)

        def save_new_name():
            new_name = entry_var.get().strip()
            if not new_name:
                messagebox.showerror("Invalid Name", "Filename cannot be empty.")
                return
            if new_name == old_name:
                edit_win.destroy()
                return
            new_path = os.path.join(FILES_FOLDER, new_name)
            if os.path.exists(new_path):
                messagebox.showerror("File Exists", "A file with that name already exists.")
                return
            try:
                os.rename(old_path, new_path)
                logger.info(f"Renamed file '{old_name}' to '{new_name}'")
                self.refresh_files_tab()
                edit_win.destroy()
            except Exception as e:
                logger.error(f"Error renaming file '{old_name}': {e}")
                messagebox.showerror("Error", f"Could not rename file:\n{e}")

        edit_win = tk.Toplevel(self.root)
        edit_win.title("Edit File Name")
        edit_win.geometry("400x150")
        edit_win.grab_set()

        ttk.Label(edit_win, text="New File Name:").pack(pady=(10, 5))
        entry_var = ttk.StringVar(value=old_name)
        entry = ttk.Entry(edit_win, textvariable=entry_var, width=50)
        entry.pack(padx=10, pady=5)
        entry.focus_set()

        btn_frame = ttk.Frame(edit_win)
        btn_frame.pack(pady=5)

        ttk.Button(btn_frame, text="Cancel", bootstyle=SECONDARY, command=edit_win.destroy).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Save", bootstyle=SUCCESS, command=save_new_name).pack(side=LEFT, padx=5)

    def refresh_files_tab(self):
        search_query = self.search_var.get().lower().strip()
        self.files_tree.delete(*self.files_tree.get_children())

        if not os.path.exists(FILES_FOLDER):
            return

        for filename in os.listdir(FILES_FOLDER):
            if search_query and search_query not in filename.lower():
                continue

            path = os.path.join(FILES_FOLDER, filename)
            if os.path.isfile(path):
                size_kb = round(os.path.getsize(path) / 1024, 2)
                mod_time = datetime.fromtimestamp(os.path.getmtime(path)).strftime('%Y-%m-%d %H:%M')
                self.files_tree.insert("", "end", values=(filename, f"{size_kb} KB", mod_time))

    def open_selected_file(self):
        selected = self.files_tree.selection()
        if not selected:
            return
        filename = self.files_tree.item(selected[0])["values"][0]
        path = os.path.join(FILES_FOLDER, filename)
        if os.path.exists(path):
            try:
                os.startfile(path)
            except Exception as e:
                logger.error(f"Failed to open file: {e}")
                messagebox.showerror("Error", f"Could not open file:\n{e}")

    def delete_selected_file(self):
        selected = self.files_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select one or more files to delete.")
            return

        file_list = [self.files_tree.item(i)["values"][0] for i in selected]
        confirm = messagebox.askyesno("Confirm Delete", f"Delete {len(file_list)} selected file(s)?")

        if confirm:
            errors = []
            for filename in file_list:
                path = os.path.join(FILES_FOLDER, filename)
                try:
                    os.remove(path)
                    logger.info(f"Deleted file: {path}")
                except Exception as e:
                    logger.error(f"Error deleting file '{path}': {e}")
                    errors.append(filename)

            self.refresh_files_tab()

            if errors:
                messagebox.showerror("Delete Errors", f"Could not delete:\n" + "\n".join(errors))
            else:
                messagebox.showinfo("Deleted", "Selected files deleted successfully.")

    @staticmethod
    def save_sent_email(name, email):
        os.makedirs("assets/client", exist_ok=True)
        filepath = "assets/client/emails.csv"
        existing = set()

        # Load existing to avoid duplicates
        if os.path.exists(filepath):
            with open(filepath, newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    existing.add((row['name'], row['email']))

        if (name, email) not in existing:
            with open(filepath, "a", newline='') as f:
                writer = csv.DictWriter(f, fieldnames=["name", "email"])
                if os.path.getsize(filepath) == 0:
                    writer.writeheader()
                writer.writerow({"name": name, "email": email})

    # Inside your DPOApp class (e.g., add to build_ui or as a new button/tab)

    def open_email_settings(self):
        win = tk.Toplevel(self.root)
        win.title("Email Settings")

        current = load_email_config()

        sender_var = tk.StringVar(value=current.get("EMAIL_SENDER", ""))
        pass_var = tk.StringVar(value=current.get("EMAIL_PASSWORD", ""))
        smtp_var = tk.StringVar(value=current.get("SMTP_SERVER", "smtp.gmail.com"))
        port_var = tk.StringVar(value=current.get("SMTP_PORT", "587"))

        ttk.Label(win, text="Sender Email:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(win, textvariable=sender_var, width=30).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(win, text="Password:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(win, textvariable=pass_var, width=30, show="*").grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(win, text="SMTP Server:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(win, textvariable=smtp_var, width=30).grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(win, text="SMTP Port:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(win, textvariable=port_var, width=30).grid(row=3, column=1, padx=5, pady=5)

        def save_and_close():
            save_email_config(
                sender_var.get().strip(),
                pass_var.get().strip(),
                smtp_var.get().strip(),
                int(port_var.get().strip())
            )
            messagebox.showinfo("Saved", "Email configuration saved.")
            win.destroy()

        ttk.Button(win, text="Save", command=save_and_close, bootstyle=SUCCESS).grid(
            row=4, column=0, columnspan=2, pady=10
        )

def get_available_templates(self):
    templates = []
    if os.path.exists(TEMPLATES_DIR):
        for file in os.listdir(TEMPLATES_DIR):
            if file.endswith(".txt"):
                templates.append(file)
    return templates
