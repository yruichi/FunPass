import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import sqlite3
from main import AdminDashboard
from for_employees import EmployeeDashboard

def center_window(root, width=800, height=600):
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    root.geometry(f"{width}x{height}+{x}+{y}")

def show_login():
    root = tk.Tk()
    root.title("FunPass - Login")
    root.configure(bg='white')
    center_window(root, 800, 600)

    main_frame = tk.Frame(root, bg='white')
    main_frame.pack(expand=True)

    # Load and display logo
    try:
        logo_path = "C:/Users/MicaellaEliab/Downloads/FunPassProjectA/FunPass__1_-removebg-preview.png"
        logo_img = Image.open(logo_path)
        logo_width = 300
        aspect_ratio = logo_img.height / logo_img.width
        logo_height = int(logo_width * aspect_ratio)
        logo_img = logo_img.resize((logo_width, logo_height))
        logo = ImageTk.PhotoImage(logo_img)
        logo_label = tk.Label(main_frame, image=logo, bg='white')
        logo_label.image = logo
        logo_label.pack(pady=20)
    except Exception as e:
        tk.Label(main_frame, text="FunPass", font=('Arial', 24, 'bold'), bg='white', fg='#4CAF50').pack(pady=20)

    # Login form
    form_frame = tk.Frame(main_frame, bg='white')
    form_frame.pack(pady=10)

    tk.Label(form_frame, text="Username:", font=('Arial', 12), bg='white').pack(pady=5)
    username_entry = tk.Entry(form_frame, font=('Arial', 12))
    username_entry.pack(pady=5)

    tk.Label(form_frame, text="Password:", font=('Arial', 12), bg='white').pack(pady=5)
    password_entry = tk.Entry(form_frame, font=('Arial', 12), show='*')
    password_entry.pack(pady=5)

    show_password = tk.BooleanVar()
    def toggle_password_visibility():
        if show_password.get():
            password_entry.config(show="")
        else:
            password_entry.config(show="*")
    tk.Checkbutton(form_frame, text="Show Password", variable=show_password, command=toggle_password_visibility, bg='white').pack(pady=5)

    def login():
        username = username_entry.get().strip()
        password = password_entry.get().strip()
        if not username or not password:
            messagebox.showwarning("Invalid Input", "Please enter both username and password")
            return
        conn = sqlite3.connect('funpass.db')
        cursor = conn.cursor()
        # Check admin first
        cursor.execute('SELECT * FROM admin WHERE username = ? AND password = ?', (username, password))
        admin = cursor.fetchone()
        if admin:
            root.destroy()
            admin_root = tk.Tk()
            AdminDashboard(admin_root)
            admin_root.mainloop()
            conn.close()
            return
        # Check employee
        cursor.execute('SELECT employee_id FROM employees WHERE username = ? AND password = ?', (username, password))
        emp = cursor.fetchone()
        if emp:
            root.destroy()
            emp_root = tk.Tk()
            EmployeeDashboard(emp_root, employee_id=emp[0])
            emp_root.mainloop()
        else:
            messagebox.showerror("Login Failed", "Invalid credentials")
        conn.close()

    tk.Button(form_frame, text="Login", font=('Arial', 12, 'bold'), bg='#4CAF50', fg='white', width=20, command=login).pack(pady=20)
    root.mainloop()

if __name__ == "__main__":
    show_login() 