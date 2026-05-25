#!/usr/bin/env python3
# passman.py - Secure Password Manager with Anti-Brute Force Protection

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
import base64
import json
import os
import sys
import pyperclip
import secrets
import string
import time

# Modern color scheme
COLORS = {
    "bg": "#1e1e1e",
    "fg": "#ffffff",
    "button_primary": "#007acc",
    "button_success": "#2ecc71",
    "button_warning": "#f39c12",
    "button_danger": "#e74c3c",
    "button_info": "#9b59b6",
    "entry_bg": "#2d2d2d",
    "tree_bg": "#252526",
    "tree_select": "#007acc"
}

class PassmanSecure:
    def __init__(self):
        self.app_dir = os.path.expanduser("~/.passman")
        self.key_file = os.path.join(self.app_dir, "key.key")
        self.data_file = os.path.join(self.app_dir, "passwords.json")
        self.show_passwords = False
        
        # Anti-brute force protection
        self.failed_attempts = 0
        self.lockout_time = None
        self.max_attempts = 5
        self.lockout_duration = 300  # 5 minutes
        
        if not os.path.exists(self.key_file):
            self.show_init_window()
        else:
            self.show_main_window()
    
    def derive_key(self, master_password: str, salt: bytes = None) -> tuple:
        if salt is None:
            salt = os.urandom(16)
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
        key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
        return key, salt
    
    def encrypt_data(self, data: dict, master_password: str) -> bytes:
        key, salt = self.derive_key(master_password)
        f = Fernet(key)
        json_data = json.dumps(data).encode()
        encrypted = f.encrypt(json_data)
        return salt + encrypted
    
    def decrypt_data(self, encrypted_data: bytes, master_password: str) -> dict:
        salt = encrypted_data[:16]
        encrypted = encrypted_data[16:]
        key, _ = self.derive_key(master_password, salt)
        f = Fernet(key)
        decrypted = f.decrypt(encrypted)
        return json.loads(decrypted.decode())
    
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure("Treeview", 
                       background=COLORS["tree_bg"],
                       foreground=COLORS["fg"],
                       fieldbackground=COLORS["tree_bg"],
                       rowheight=30,
                       font=('Arial', 10))
        
        style.configure("Treeview.Heading",
                       background="#3c3c3c",
                       foreground=COLORS["fg"],
                       font=('Arial', 11, 'bold'))
        
        style.map('Treeview',
                 background=[('selected', COLORS["tree_select"])])
        
        style.map('Treeview.Heading',
                 background=[('active', '#4c4c4c')])
    
    def show_init_window(self):
        self.root = tk.Tk()
        self.root.title("🔐 Passman - Initial Setup")
        self.root.geometry("450x400")
        self.root.resizable(False, False)
        self.root.configure(bg=COLORS["bg"])
        
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (450 // 2)
        y = (self.root.winfo_screenheight() // 2) - (400 // 2)
        self.root.geometry(f"+{x}+{y}")
        
        main_frame = tk.Frame(self.root, bg=COLORS["bg"])
        main_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        tk.Label(main_frame, text="🔐 Passman", font=("Arial", 24, "bold"),
                bg=COLORS["bg"], fg=COLORS["fg"]).pack(pady=20)
        
        tk.Label(main_frame, text="Set up your master password",
                bg=COLORS["bg"], fg=COLORS["fg"]).pack()
        
        tk.Label(main_frame, text="Master Password:", bg=COLORS["bg"],
                fg=COLORS["fg"]).pack(pady=(20, 5))
        
        self.master_pass = tk.Entry(main_frame, show="*", width=30,
                                    font=('Arial', 11), bg=COLORS["entry_bg"],
                                    fg=COLORS["fg"], insertbackground=COLORS["fg"])
        self.master_pass.pack()
        
        tk.Label(main_frame, text="Confirm Password:", bg=COLORS["bg"],
                fg=COLORS["fg"]).pack(pady=(10, 5))
        
        self.master_pass2 = tk.Entry(main_frame, show="*", width=30,
                                     font=('Arial', 11), bg=COLORS["entry_bg"],
                                     fg=COLORS["fg"], insertbackground=COLORS["fg"])
        self.master_pass2.pack()
        
        tk.Button(main_frame, text="🔐 Initialize", command=self.initialize,
                 bg=COLORS["button_success"], fg="white", font=('Arial', 10, 'bold'),
                 padx=20, pady=5, cursor="hand2", relief="flat").pack(pady=30)
        
        self.root.mainloop()
    
    def initialize(self):
        master = self.master_pass.get()
        master2 = self.master_pass2.get()
        
        if not master or not master2:
            messagebox.showerror("Error", "Fields cannot be empty")
            return
        if master != master2:
            messagebox.showerror("Error", "Passwords do not match")
            return
        if len(master) < 4:
            messagebox.showerror("Error", "Password must be at least 4 characters")
            return
        
        try:
            os.makedirs(self.app_dir, exist_ok=True)
            encrypted = self.encrypt_data({}, master)
            with open(self.data_file, "wb") as f:
                f.write(encrypted)
            with open(self.key_file, "wb") as f:
                f.write(b"initialized")
            messagebox.showinfo("Success", "✅ Passman initialized successfully")
            self.root.destroy()
            self.show_main_window()
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def authenticate(self):
        """Authentication with anti-brute force protection"""
        
        # Check if locked out
        if self.lockout_time:
            elapsed = time.time() - self.lockout_time
            if elapsed < self.lockout_duration:
                remaining = int(self.lockout_duration - elapsed)
                minutes = remaining // 60
                seconds = remaining % 60
                messagebox.showerror(
                    "🔒 Account Locked", 
                    f"Too many failed attempts.\n"
                    f"Wait {minutes}m {seconds}s before trying again."
                )
                return False
            else:
                self.failed_attempts = 0
                self.lockout_time = None
        
        # Show remaining attempts
        if self.failed_attempts > 0:
            remaining = self.max_attempts - self.failed_attempts
            msg = f"Remaining attempts: {remaining}"
        else:
            msg = "Enter your master password"
        
        password = simpledialog.askstring("🔐 Authentication", msg, show="*")
        if not password:
            return False
        
        try:
            with open(self.data_file, "rb") as f:
                encrypted_data = f.read()
            self.decrypt_data(encrypted_data, password)
            self.current_password = password
            self.failed_attempts = 0
            self.lockout_time = None
            return True
            
        except Exception:
            self.failed_attempts += 1
            remaining = self.max_attempts - self.failed_attempts
            
            if self.failed_attempts >= self.max_attempts:
                self.lockout_time = time.time()
                messagebox.showerror(
                    "❌ Access Denied", 
                    f"Incorrect password.\n\n"
                    f"You have exceeded {self.max_attempts} attempts.\n"
                    f"System locked for {self.lockout_duration // 60} minutes."
                )
                return False
            else:
                messagebox.showerror(
                    "❌ Incorrect Password", 
                    f"You have {remaining} attempt(s) remaining before lockout."
                )
                return False
    
    def load_data(self):
        try:
            with open(self.data_file, "rb") as f:
                encrypted_data = f.read()
            return self.decrypt_data(encrypted_data, self.current_password)
        except:
            return {}
    
    def save_data(self, data):
        try:
            encrypted = self.encrypt_data(data, self.current_password)
            with open(self.data_file, "wb") as f:
                f.write(encrypted)
            return True
        except:
            return False
    
    def generate_password(self):
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(chars) for _ in range(16))
    
    def copy_to_clipboard(self, text):
        try:
            pyperclip.copy(text)
            self.status_label.config(text="✅ Copied to clipboard")
            self.root.after(2000, lambda: self.status_label.config(text="Ready"))
        except:
            messagebox.showerror("Error", "Could not copy to clipboard")
    
    def show_main_window(self):
        if not self.authenticate():
            sys.exit(0)
        
        self.root = tk.Tk()
        self.root.title("🔐 Passman - Password Manager")
        self.root.geometry("1000x650")
        self.root.configure(bg=COLORS["bg"])
        
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (1000 // 2)
        y = (self.root.winfo_screenheight() // 2) - (650 // 2)
        self.root.geometry(f"+{x}+{y}")
        
        self.setup_styles()
        
        # Header
        header = tk.Frame(self.root, bg=COLORS["bg"], height=70)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(header, text="🔐 Passman", font=("Arial", 24, "bold"),
                bg=COLORS["bg"], fg=COLORS["fg"]).pack(pady=15)
        
        # Buttons
        button_frame = tk.Frame(self.root, bg=COLORS["bg"])
        button_frame.pack(fill="x", padx=20, pady=10)
        
        btn_config = {"font": ('Arial', 10, 'bold'), "fg": "white",
                     "padx": 15, "pady": 5, "cursor": "hand2", "relief": "flat"}
        
        tk.Button(button_frame, text="➕ Add", command=self.add_entry,
                 bg=COLORS["button_primary"], **btn_config).pack(side="left", padx=5)
        
        tk.Button(button_frame, text="✏️ Edit", command=self.edit_entry,
                 bg=COLORS["button_warning"], **btn_config).pack(side="left", padx=5)
        
        tk.Button(button_frame, text="🗑️ Delete", command=self.delete_entry,
                 bg=COLORS["button_danger"], **btn_config).pack(side="left", padx=5)
        
        tk.Button(button_frame, text="👁️ Show/Hide", command=self.toggle_passwords,
                 bg=COLORS["button_info"], **btn_config).pack(side="left", padx=5)
        
        tk.Button(button_frame, text="📋 View Details", command=self.show_details,
                 bg=COLORS["button_primary"], **btn_config).pack(side="left", padx=5)
        
        # Search
        search_frame = tk.Frame(self.root, bg=COLORS["bg"])
        search_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(search_frame, text="🔍 Search:", bg=COLORS["bg"], fg=COLORS["fg"],
                font=('Arial', 10)).pack(side="left", padx=5)
        
        self.search_entry = tk.Entry(search_frame, width=40, font=('Arial', 10),
                                     bg=COLORS["entry_bg"], fg=COLORS["fg"],
                                     insertbackground=COLORS["fg"])
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_list())
        
        tk.Button(search_frame, text="Clear", command=self.clear_search,
                 bg="#7f8c8d", **btn_config).pack(side="left", padx=5)
        
        # Treeview
        tree_frame = tk.Frame(self.root, bg=COLORS["bg"])
        tree_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.tree = ttk.Treeview(tree_frame, columns=("Username", "Password"),
                                  show="tree", yscrollcommand=scrollbar.set)
        self.tree.heading("#0", text="Service", anchor="w")
        self.tree.heading("Username", text="Username", anchor="w")
        self.tree.heading("Password", text="Password", anchor="w")
        
        self.tree.column("#0", width=350)
        self.tree.column("Username", width=300)
        self.tree.column("Password", width=250)
        
        self.tree.pack(fill="both", expand=True)
        scrollbar.config(command=self.tree.yview)
        
        self.tree.bind("<Double-1>", self.on_double_click)
        
        # Status bar
        self.status_label = tk.Label(self.root, text="Ready", bg="#2c3e50", fg=COLORS["fg"],
                                     font=('Arial', 9), anchor="w")
        self.status_label.pack(fill="x", side="bottom")
        
        self.refresh_list()
        self.root.mainloop()
    
    def refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.data = self.load_data()
        search = self.search_entry.get().lower()
        
        for service, info in self.data.items():
            if search in service.lower():
                if self.show_passwords:
                    pass_display = info["password"]
                else:
                    pass_display = "••••••••"
                self.tree.insert("", "end", text=service, values=(info["username"], pass_display))
        
        self.status_label.config(text=f"📊 Total: {len(self.data)} passwords")
    
    def toggle_passwords(self):
        self.show_passwords = not self.show_passwords
        self.refresh_list()
    
    def on_double_click(self, event):
        selected = self.tree.selection()
        if selected:
            service = self.tree.item(selected[0])["text"]
            self.copy_to_clipboard(self.data[service]["password"])
    
    def get_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a service first")
            return None
        return self.tree.item(selected[0])["text"]
    
    def add_entry(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Password")
        dialog.geometry("500x500")
        dialog.configure(bg=COLORS["bg"])
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (500 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        main_frame = tk.Frame(dialog, bg=COLORS["bg"])
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(main_frame, text="➕ New Password", font=("Arial", 18, "bold"),
                bg=COLORS["bg"], fg=COLORS["fg"]).pack(pady=20)
        
        tk.Label(main_frame, text="Service:", bg=COLORS["bg"], fg=COLORS["fg"],
                anchor="w").pack(fill="x", padx=20, pady=(10, 0))
        service_entry = tk.Entry(main_frame, width=50, font=('Arial', 11),
                                 bg=COLORS["entry_bg"], fg=COLORS["fg"],
                                 insertbackground=COLORS["fg"])
        service_entry.pack(pady=5, padx=20)
        
        tk.Label(main_frame, text="Username:", bg=COLORS["bg"], fg=COLORS["fg"],
                anchor="w").pack(fill="x", padx=20, pady=(10, 0))
        username_entry = tk.Entry(main_frame, width=50, font=('Arial', 11),
                                  bg=COLORS["entry_bg"], fg=COLORS["fg"],
                                  insertbackground=COLORS["fg"])
        username_entry.pack(pady=5, padx=20)
        
        tk.Label(main_frame, text="Password:", bg=COLORS["bg"], fg=COLORS["fg"],
                anchor="w").pack(fill="x", padx=20, pady=(10, 0))
        password_entry = tk.Entry(main_frame, width=50, font=('Arial', 11),
                                  bg=COLORS["entry_bg"], fg=COLORS["fg"],
                                  insertbackground=COLORS["fg"], show="*")
        password_entry.pack(pady=5, padx=20)
        
        def gen_pass():
            password_entry.delete(0, "end")
            password_entry.insert(0, self.generate_password())
        
        tk.Button(main_frame, text="🔑 Generate Secure Password", command=gen_pass,
                 bg=COLORS["button_success"], fg="white", font=('Arial', 10),
                 padx=10, pady=5, cursor="hand2", relief="flat").pack(pady=10)
        
        def save():
            service = service_entry.get().strip()
            username = username_entry.get().strip()
            password = password_entry.get().strip()
            
            if not service or not username or not password:
                messagebox.showerror("Error", "All fields are required")
                return
            
            if service in self.data:
                if not messagebox.askyesno("Confirm", f"Overwrite {service}?"):
                    return
            
            self.data[service] = {"username": username, "password": password}
            if self.save_data(self.data):
                messagebox.showinfo("Success", f"✅ Saved: {service}")
                dialog.destroy()
                self.refresh_list()
        
        tk.Button(main_frame, text="💾 Save", command=save,
                 bg=COLORS["button_primary"], fg="white", font=('Arial', 10, 'bold'),
                 padx=20, pady=8, cursor="hand2", relief="flat").pack(pady=20)
        
        tk.Button(main_frame, text="❌ Cancel", command=dialog.destroy,
                 bg="#7f8c8d", fg="white", font=('Arial', 10),
                 padx=20, pady=5, cursor="hand2", relief="flat").pack()
    
    def edit_entry(self):
        service = self.get_selected()
        if not service:
            return
        
        data = self.data[service]
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Edit - {service}")
        dialog.geometry("500x450")
        dialog.configure(bg=COLORS["bg"])
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (450 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        main_frame = tk.Frame(dialog, bg=COLORS["bg"])
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(main_frame, text=f"✏️ Editing {service}", font=("Arial", 18, "bold"),
                bg=COLORS["bg"], fg=COLORS["fg"]).pack(pady=20)
        
        tk.Label(main_frame, text="Username:", bg=COLORS["bg"], fg=COLORS["fg"],
                anchor="w").pack(fill="x", padx=20)
        username_entry = tk.Entry(main_frame, width=50, font=('Arial', 11),
                                  bg=COLORS["entry_bg"], fg=COLORS["fg"],
                                  insertbackground=COLORS["fg"])
        username_entry.insert(0, data["username"])
        username_entry.pack(pady=5, padx=20)
        
        tk.Label(main_frame, text="Password:", bg=COLORS["bg"], fg=COLORS["fg"],
                anchor="w").pack(fill="x", padx=20, pady=(10, 0))
        password_entry = tk.Entry(main_frame, width=50, font=('Arial', 11),
                                  bg=COLORS["entry_bg"], fg=COLORS["fg"],
                                  insertbackground=COLORS["fg"], show="*")
        password_entry.insert(0, data["password"])
        password_entry.pack(pady=5, padx=20)
        
        def save():
            self.data[service] = {"username": username_entry.get(), "password": password_entry.get()}
            if self.save_data(self.data):
                messagebox.showinfo("Success", "✅ Updated")
                dialog.destroy()
                self.refresh_list()
        
        tk.Button(main_frame, text="💾 Save Changes", command=save,
                 bg=COLORS["button_primary"], fg="white", font=('Arial', 10, 'bold'),
                 padx=20, pady=8, cursor="hand2", relief="flat").pack(pady=20)
        
        tk.Button(main_frame, text="❌ Cancel", command=dialog.destroy,
                 bg="#7f8c8d", fg="white", font=('Arial', 10),
                 padx=20, pady=5, cursor="hand2", relief="flat").pack()
    
    def delete_entry(self):
        service = self.get_selected()
        if not service:
            return
        
        if messagebox.askyesno("Confirm", f"Delete {service}?"):
            del self.data[service]
            if self.save_data(self.data):
                messagebox.showinfo("Success", f"✅ Deleted: {service}")
                self.refresh_list()
    
    def show_details(self):
        service = self.get_selected()
        if not service:
            return
        
        data = self.data[service]
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Details - {service}")
        dialog.geometry("500x400")
        dialog.configure(bg=COLORS["bg"])
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (400 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        main_frame = tk.Frame(dialog, bg=COLORS["bg"])
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(main_frame, text=f"🔐 {service}", font=("Arial", 18, "bold"),
                bg=COLORS["bg"], fg=COLORS["fg"]).pack(pady=20)
        
        user_frame = tk.Frame(main_frame, bg=COLORS["bg"])
        user_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(user_frame, text=f"👤 Username: {data['username']}",
                bg=COLORS["bg"], fg=COLORS["fg"], font=('Arial', 11)).pack(side="left")
        
        tk.Button(user_frame, text="📋 Copy", command=lambda: self.copy_to_clipboard(data['username']),
                 bg=COLORS["button_primary"], fg="white", font=('Arial', 9),
                 padx=10, pady=2, cursor="hand2", relief="flat").pack(side="right")
        
        pass_frame = tk.Frame(main_frame, bg=COLORS["bg"])
        pass_frame.pack(fill="x", padx=20, pady=10)
        
        self.detail_pass_label = tk.Label(pass_frame, text="••••••••",
                                         bg=COLORS["bg"], fg=COLORS["fg"], font=('Arial', 11))
        self.detail_pass_label.pack(side="left")
        
        def toggle():
            if self.detail_pass_label.cget('text') == "••••••••":
                self.detail_pass_label.config(text=data['password'])
                toggle_btn.config(text="🙈 Hide")
            else:
                self.detail_pass_label.config(text="••••••••")
                toggle_btn.config(text="👁️ Show")
        
        toggle_btn = tk.Button(pass_frame, text="👁️ Show", command=toggle,
                              bg=COLORS["button_info"], fg="white", font=('Arial', 9),
                              padx=10, pady=2, cursor="hand2", relief="flat")
        toggle_btn.pack(side="right", padx=5)
        
        tk.Button(pass_frame, text="📋 Copy", command=lambda: self.copy_to_clipboard(data['password']),
                 bg=COLORS["button_success"], fg="white", font=('Arial', 9),
                 padx=10, pady=2, cursor="hand2", relief="flat").pack(side="right", padx=5)
        
        tk.Button(main_frame, text="Close", command=dialog.destroy,
                 bg="#7f8c8d", fg="white", font=('Arial', 10, 'bold'),
                 padx=30, pady=5, cursor="hand2", relief="flat").pack(pady=30)
    
    def clear_search(self):
        self.search_entry.delete(0, "end")
        self.refresh_list()

if __name__ == "__main__":
    app = PassmanSecure()
