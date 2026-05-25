#!/usr/bin/env python3
# passman.py - UI for Passman

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import pyperclip
import sys

from core import PassmanCore

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

class PassmanUI:
    def __init__(self):
        self.core = PassmanCore()
        self.show_passwords = False
        
        if not self.core.exists():
            self.show_init_window()
        else:
            self.show_login()
    
    def setup_treeview_styles(self):
        """Configure treeview styles"""
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
    
    def center_window(self, window, width, height):
        """Center window on screen"""
        window.update_idletasks()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f"+{x}+{y}")
    
    def show_init_window(self):
        """First time setup window"""
        self.root = tk.Tk()
        self.root.title("🔐 Passman - Setup")
        self.root.geometry("450x400")
        self.root.resizable(False, False)
        self.root.configure(bg=COLORS["bg"])
        self.center_window(self.root, 450, 400)
        
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
        
        def init():
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
            
            self.core.init_db(master)
            messagebox.showinfo("Success", "✅ Passman initialized")
            self.root.destroy()
            self.show_login()
        
        tk.Button(main_frame, text="🔐 Initialize", command=init,
                 bg=COLORS["button_success"], fg="white", font=('Arial', 10, 'bold'),
                 padx=20, pady=5, cursor="hand2", relief="flat").pack(pady=30)
        
        self.root.mainloop()
    
    def show_login(self):
        """Show login dialog"""
        # Check if locked first
        locked, remaining = self.core.is_locked()
        if locked:
            minutes = int(remaining // 60)
            seconds = int(remaining % 60)
            messagebox.showerror("Locked", 
                f"Too many failed attempts.\n"
                f"Wait {minutes}m {seconds}s before trying again.")
            sys.exit(0)
        
        password = simpledialog.askstring("🔐 Authentication", "Enter master password:", show="*")
        if not password:
            sys.exit(0)
        
        success, remaining = self.core.authenticate(password)
        
        if not success:
            if remaining == -2:
                messagebox.showerror("Error", 
                    "❌ Password database is corrupted!\n\n"
                    "The database file appears to be damaged.\n"
                    f"Location: {self.core.data_file}\n\n"
                    "Try restoring from backup or delete the .passman folder and reinitialize.")
                sys.exit(0)
            elif remaining == -1:
                locked, remaining_time = self.core.is_locked()
                if locked:
                    minutes = int(remaining_time // 60)
                    seconds = int(remaining_time % 60)
                    messagebox.showerror("Locked", 
                        f"Too many failed attempts.\n"
                        f"Wait {minutes}m {seconds}s before trying again.")
                else:
                    messagebox.showerror("Locked", "Too many failed attempts. Try again later.")
                sys.exit(0)
            elif remaining > 0:
                messagebox.showerror("Error", f"Incorrect password. {remaining} attempts left.")
                self.show_login()  # Try again
            else:
                messagebox.showerror("Error", "Authentication failed")
                sys.exit(0)
        else:
            self.show_main_window()
    
    def show_main_window(self):
        """Main application window"""
        self.root = tk.Tk()
        self.root.title("🔐 Passman - Password Manager")
        self.root.geometry("1000x650")
        self.root.configure(bg=COLORS["bg"])
        self.center_window(self.root, 1000, 650)
        
        # Apply treeview styles
        self.setup_treeview_styles()
        
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
        
        tk.Button(button_frame, text="📋 Details", command=self.show_details,
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
        
        # Treeview with scrollbar
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
        """Refresh the password list"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        data = self.core.get_all()
        search = self.search_entry.get().lower()
        
        for service, info in data.items():
            if search in service.lower():
                if self.show_passwords:
                    pass_display = info["password"]
                else:
                    pass_display = "••••••••"
                self.tree.insert("", "end", text=service, values=(info["username"], pass_display))
        
        self.status_label.config(text=f"📊 Total: {len(data)} passwords")
    
    def toggle_passwords(self):
        """Toggle password visibility"""
        self.show_passwords = not self.show_passwords
        self.refresh_list()
    
    def on_double_click(self, event):
        """Double click to copy password"""
        selected = self.tree.selection()
        if selected:
            service = self.tree.item(selected[0])["text"]
            data = self.core.get(service)
            if data:
                self.copy_to_clipboard(data["password"])
    
    def copy_to_clipboard(self, text):
        """Copy text to clipboard"""
        try:
            pyperclip.copy(text)
            self.status_label.config(text="✅ Copied to clipboard")
            self.root.after(2000, lambda: self.status_label.config(text="Ready"))
        except:
            messagebox.showerror("Error", "Could not copy to clipboard")
    
    def get_selected(self):
        """Get currently selected service"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a service first")
            return None
        return self.tree.item(selected[0])["text"]
    
    def add_entry(self):
        """Add new password dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Password")
        dialog.geometry("500x500")
        dialog.configure(bg=COLORS["bg"])
        dialog.transient(self.root)
        dialog.grab_set()
        self.center_window(dialog, 500, 500)
        
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
            password_entry.insert(0, self.core.generate_password())
        
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
            
            if service in self.core.get_all():
                if not messagebox.askyesno("Confirm", f"Overwrite {service}?"):
                    return
            
            if self.core.add(service, username, password):
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
        """Edit existing password dialog"""
        service = self.get_selected()
        if not service:
            return
        
        data = self.core.get(service)
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Edit - {service}")
        dialog.geometry("500x450")
        dialog.configure(bg=COLORS["bg"])
        dialog.transient(self.root)
        dialog.grab_set()
        self.center_window(dialog, 500, 450)
        
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
            if self.core.update(service, username_entry.get(), password_entry.get()):
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
        """Delete password entry"""
        service = self.get_selected()
        if not service:
            return
        
        if messagebox.askyesno("Confirm", f"Delete {service}?"):
            if self.core.delete(service):
                messagebox.showinfo("Success", f"✅ Deleted: {service}")
                self.refresh_list()
    
    def show_details(self):
        """Show password details dialog"""
        service = self.get_selected()
        if not service:
            return
        
        data = self.core.get(service)
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Details - {service}")
        dialog.geometry("500x400")
        dialog.configure(bg=COLORS["bg"])
        dialog.transient(self.root)
        dialog.grab_set()
        self.center_window(dialog, 500, 400)
        
        main_frame = tk.Frame(dialog, bg=COLORS["bg"])
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(main_frame, text=f"🔐 {service}", font=("Arial", 18, "bold"),
                bg=COLORS["bg"], fg=COLORS["fg"]).pack(pady=20)
        
        # Username
        user_frame = tk.Frame(main_frame, bg=COLORS["bg"])
        user_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(user_frame, text=f"👤 Username: {data['username']}",
                bg=COLORS["bg"], fg=COLORS["fg"], font=('Arial', 11)).pack(side="left")
        
        tk.Button(user_frame, text="📋 Copy", command=lambda: self.copy_to_clipboard(data['username']),
                 bg=COLORS["button_primary"], fg="white", font=('Arial', 9),
                 padx=10, pady=2, cursor="hand2", relief="flat").pack(side="right")
        
        # Password
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
        """Clear search box"""
        self.search_entry.delete(0, "end")
        self.refresh_list()

if __name__ == "__main__":
    app = PassmanUI()
