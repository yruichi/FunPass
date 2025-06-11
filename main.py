import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import sqlite3
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkcalendar import DateEntry
import pandas as pd
from shared import create_database, BaseWindow
import time  # Add missing import

# database setup
def create_database():
    conn = sqlite3.connect('funpass.db')
    cursor = conn.cursor()

    # to create admin table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    ''')

    # to insert default admin if not exists
    cursor.execute('INSERT OR IGNORE INTO admin (username, password) VALUES (?, ?)',
                  ('admin', 'admin123'))

    # to create employees table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            express_pass INTEGER DEFAULT 0,
            junior_pass INTEGER DEFAULT 0,
            regular_pass INTEGER DEFAULT 0,
            student_pass INTEGER DEFAULT 0,
            pwd_pass INTEGER DEFAULT 0,
            senior_citizen_pass INTEGER DEFAULT 0
        )
    ''')

    # to create customers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            ticket_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            amount REAL NOT NULL,
            booked_date TEXT NOT NULL,
            purchased_date TEXT NOT NULL,
            pass_type TEXT NOT NULL,
            employee_id INTEGER,
            FOREIGN KEY (employee_id) REFERENCES employees (employee_id)
        )
    ''')

    # to create cancellations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cancellations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            reasons TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            amount REAL NOT NULL,
            booked_date TEXT NOT NULL,
            purchased_date TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            FOREIGN KEY (ticket_id) REFERENCES customers (ticket_id)
        )
    ''')

    # to create pricing table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pricing (
            pass_type TEXT PRIMARY KEY,
            price REAL NOT NULL
        )
    ''')

    # to insert or update default prices
    default_prices = [
        ('Express Pass', 2300.00),
        ('Junior Pass', 900.00),
        ('Regular Pass', 1300.00),
        ('Student Pass', 1300.00),
        ('Senior Citizen Pass', 900.00),
        ('PWD Pass', 900.00)
    ]
    
    cursor.executemany('''
        INSERT OR REPLACE INTO pricing (pass_type, price)
        VALUES (?, ?)
    ''', default_prices)

    conn.commit()
    conn.close()

class AdminDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("FunPass - Admin Dashboard")
        self.root.state('zoomed')
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.price_entries = {}  # Initialize price entries dictionary
        self.create_sidebar()
        self.content_frame = tk.Frame(self.root, bg='white')
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.show_dashboard()

    def create_sidebar(self):
        sidebar = tk.Frame(self.root, bg='#ECCD93', width=350)
        sidebar.grid(row=0, column=0, sticky="ns")
        sidebar.grid_propagate(False)

            # to add logo at the top of sidebar
        try:
            logo_path = "C:/Users/MicaellaEliab/Downloads/FunPassProjectA/FunPass__1_-removebg-preview.png"
            logo_img = Image.open(logo_path)
            # to resize logo to fit sidebar width while maintaining aspect ratio
            logo_width = 220  
            aspect_ratio = logo_img.height / logo_img.width
            logo_height = int(logo_width * aspect_ratio)
            logo_img = logo_img.resize((logo_width, logo_height))
            
            self.sidebar_logo = ImageTk.PhotoImage(logo_img)
            logo_label = tk.Label(sidebar, image=self.sidebar_logo, bg='#ECCD93')
            logo_label.pack(pady=20)
        except Exception as e:
            print(f"Error loading sidebar logo: {e}")

        # to create sidebar buttons
        buttons = [
            ("Dashboard", self.show_dashboard),
            ("Rides", self.show_rides),
            ("Employee Management", self.show_employee_management),
            ("Customers", self.show_customers),
            ("Cancellations & Refunds", self.show_cancellations),
            ("Pricing", self.show_pricing),
            ("Logout", self.logout)
        ]

        for text, command in buttons:
            btn = tk.Button(sidebar, text=text, command=command,
                          bg='#ECCD93', fg='black', font=('Arial', 10, 'bold'),
                          bd=0, pady=15, width=20)
            btn.pack(pady=2)
            btn.bind('<Enter>', lambda e, btn=btn: btn.configure(bg='#ECCD93'))
            btn.bind('<Leave>', lambda e, btn=btn: btn.configure(bg='#ECCD93'))

    def clear_content(self):
        # to properly destroy all widgets in the content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        # to ensure the content frame itself exists
        if not hasattr(self, 'content_frame'):
            self.content_frame = tk.Frame(self.root, bg='white')
            self.content_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    def show_dashboard(self):
        self.clear_content()
        
        # to add dashboard title
        dashboard_title = tk.Label(self.content_frame, text="Dashboard", font=('Arial', 18, 'bold'), bg='white', anchor='w')
        dashboard_title.pack(pady=(10, 0), padx=20, anchor='w')
        dashboard_subtitle = tk.Label(self.content_frame, text="View and Manage FunPass: Amusement Park Ticketing System", font=('Arial', 12), fg='#6b7280', bg='white', anchor='w')
        dashboard_subtitle.pack(pady=(0, 10), padx=20, anchor='w')
        
        # to create top bar with date and time
        top_bar = tk.Frame(self.content_frame, bg='white')
        top_bar.pack(fill=tk.X, pady=10)

        # to create date and time display with better formatting
        time_frame = tk.Frame(top_bar, bg='white', relief='solid', bd=1)
        time_frame.pack(side=tk.RIGHT, padx=20, pady=5)
        
        self.date_label = tk.Label(time_frame, font=('Arial', 12, 'bold'), bg='white')
        self.date_label.pack(side=tk.LEFT, padx=10)
        
        self.time_label = tk.Label(time_frame, font=('Arial', 12), bg='white')
        self.time_label.pack(side=tk.LEFT, padx=10)
        
        self.update_time()

        # to create statistics overview section
        stats_frame = tk.LabelFrame(self.content_frame, text="Overview", 
                                  bg='white', font=('Arial', 12, 'bold'))
        stats_frame.pack(fill=tk.X, pady=10, padx=5)

        # to create a grid for statistics
        for i in range(2):
            stats_frame.grid_columnconfigure(i, weight=1)

        # to get statistics from database
        conn = sqlite3.connect('funpass.db')
        cursor = conn.cursor()
        
        # to get total sales
        cursor.execute('SELECT SUM(amount) FROM customers')
        total_sales = cursor.fetchone()[0] or 0
        
        # to get active employees
        cursor.execute('SELECT COUNT(*) FROM employees')
        active_employees = cursor.fetchone()[0] or 0
        
        # to get total tickets sold
        cursor.execute('SELECT SUM(quantity) FROM customers')
        total_tickets = cursor.fetchone()[0] or 0
        
        # to get total pending refunds
        cursor.execute('SELECT COUNT(*) FROM cancellations WHERE status="Pending"')
        pending_refunds = cursor.fetchone()[0] or 0
        
        conn.close()

            # to create statistic cards
        stats_data = [
            ("Total Sales", f"₱{total_sales:,.2f}", "#2196F3"),
            ("Active Employees", str(active_employees), "#4CAF50"),
            ("Total Tickets Sold", str(total_tickets), "#FF9800"),
            ("Pending Refunds", str(pending_refunds), "#f44336")
        ]

        for idx, (label, value, color) in enumerate(stats_data):
            stat_card = tk.Frame(stats_frame, bg='white', relief='solid', bd=1)
            stat_card.grid(row=idx//2, column=idx%2, padx=10, pady=5, sticky='ew')
            
            tk.Label(stat_card, text=label, font=('Arial', 10), 
                    bg='white').pack(pady=2)
            tk.Label(stat_card, text=value, font=('Arial', 16, 'bold'), 
                    fg=color, bg='white').pack(pady=2)

        # to create revenue section with smaller graph
        revenue_frame = tk.LabelFrame(self.content_frame, text="Revenue Overview", 
                                    bg='white', font=('Arial', 12, 'bold'))
        revenue_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # to create filter options
        filter_frame = tk.Frame(revenue_frame, bg='white')
        filter_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(filter_frame, text="Period:", bg='white').pack(side=tk.LEFT, padx=5)
        period = ttk.Combobox(filter_frame, 
                            values=["Today", "This Month", "Last 6 Months"])
        period.pack(side=tk.LEFT, padx=5)
        period.set("This Month")

        # to create smaller revenue graph
        fig, ax = plt.subplots(figsize=(2.5, 2))  
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
        revenue = pd.Series(index=dates, data=range(100, 3200, 100))
        revenue.plot(ax=ax)
        ax.set_title('Revenue Over Time')
        plt.tight_layout()  
        
        canvas = FigureCanvasTkAgg(fig, master=revenue_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def update_time(self):
        try:
            current = datetime.now()
            current_time = current.strftime("%m/%d/%Y %H:%M:%S")
            if hasattr(self, 'time_label'):
                self.time_label.config(text=current_time)
            if hasattr(self, 'date_label'):
                self.date_label.config(text=current.strftime("%A, %B %d, %Y"))
            self.root.after(1000, self.update_time)
        except Exception as e:
            print(f"Error updating time: {e}")

    def show_rides(self):
        self.clear_content()
        
        # to create main frame for rides
        rides_frame = tk.Frame(self.content_frame, bg='white')
        rides_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # to create title frame
        header_frame = tk.Frame(rides_frame, bg='white')
        header_frame.pack(fill=tk.X, pady=(0, 20))

        # to create title
        title = tk.Label(header_frame, text="Pass Types and Inclusions", 
                        font=('Arial', 16, 'bold'), bg='white')
        title.pack(side=tk.LEFT, pady=(0, 10))

        # to create a canvas with scrollbar
        canvas = tk.Canvas(rides_frame, bg='white')
        scrollbar = ttk.Scrollbar(rides_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white')

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # to define pass types and their descriptions
        pass_descriptions = [
            ("Express Pass", """• Priority access to all rides and attractions
• Skip regular lines
• Access to exclusive Express Pass lanes
• Unlimited rides all day
• Special discounts at food stalls
• Free locker usage
• Free parking
• Exclusive souvenir"""),
            
            ("Junior Pass", """• Access to all kid-friendly rides
• Special access to children's play areas
• Meet and greet with mascots
• Free snack pack
• Age requirement: 4-12 years old
• Free kid's meal
• Free face painting
• Access to kids' workshops"""),
            
            ("Regular Pass", """• Standard access to all rides and attractions
• Regular queue lines
• Full day access
• Basic amenities access
• Suitable for all ages
• Free water bottle
• Access to rest areas
• Standard locker rental rates"""),
            
            ("Student Pass", """• Access to all rides and attractions
• Special student discount
• Valid student ID required
• Available on weekdays only
• Includes free locker use
• Free study area access
• Student meal discount
• Free WiFi access"""),
            
            ("Senior Citizen Pass", """• Access to all rides and attractions
• Priority queuing at selected rides
• Special assistance available
• Senior citizen ID required
• Includes free refreshments
• Access to senior's lounge
• Free health monitoring
• Special meal options"""),
            
            ("PWD Pass", """• Access to all rides and attractions
• Priority queuing at all rides
• Special assistance available
• PWD ID required
• Companion gets 50% discount
• Free wheelchair service
• Dedicated assistance staff
• Special facilities access""")
        ]

        for pass_type, description in pass_descriptions:
            # to create frame for each pass type
            pass_frame = tk.Frame(scrollable_frame, bg='white', bd=1, relief='solid')
            pass_frame.pack(fill=tk.X, pady=5, padx=10)

            # to create header frame with pass type
            header = tk.Frame(pass_frame, bg='#f0f0f0')
            header.pack(fill=tk.X)

            # to create pass type header
            tk.Label(header, text=pass_type, font=('Arial', 12, 'bold'), 
                    bg='#f0f0f0', padx=10, pady=5).pack(anchor='w')

            # description with bullet points
            desc_label = tk.Label(pass_frame, text=description, font=('Arial', 11),
                               bg='white', justify=tk.LEFT, anchor='w', wraplength=600)
            desc_label.pack(fill=tk.X, padx=20, pady=10)

        # to pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def add_ride_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Pass Type")
        dialog.geometry("600x500")
        dialog.configure(bg='white')

        # to create main frame
        main_frame = tk.Frame(dialog, bg='white', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # to create pass type
        tk.Label(main_frame, text="Pass Type:", font=('Arial', 11, 'bold'), 
                bg='white').pack(anchor='w', pady=(0, 5))
        pass_type_entry = tk.Entry(main_frame, font=('Arial', 11), width=40)
        pass_type_entry.pack(fill=tk.X, pady=(0, 15))

        # to create description
        tk.Label(main_frame, text="Description:", font=('Arial', 11, 'bold'), 
                bg='white').pack(anchor='w', pady=(0, 5))
        description_text = tk.Text(main_frame, font=('Arial', 11), height=15)
        description_text.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        def save_new_ride():
            pass_type = pass_type_entry.get().strip()
            description = description_text.get("1.0", tk.END).strip()

            if not pass_type or not description:
                messagebox.showwarning("Invalid Input", 
                                     "Please fill in both pass type and description.")
                return

            try:
                conn = sqlite3.connect('funpass.db')
                cursor = conn.cursor()
                cursor.execute('INSERT INTO rides (pass_type, description) VALUES (?, ?)',
                             (pass_type, description))
                conn.commit()
                conn.close()
                dialog.destroy()
                self.show_rides()  # Refresh the rides page
                messagebox.showinfo("Success", "New pass type added successfully!")
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "This pass type already exists!")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {str(e)}")

        # to create buttons frame
        btn_frame = tk.Frame(main_frame, bg='white')
        btn_frame.pack(pady=20)

        tk.Button(btn_frame, text="Save", command=save_new_ride,
                 bg='#4CAF50', fg='white', font=('Arial', 11),
                 width=10).pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame, text="Cancel", command=dialog.destroy,
                 bg='#f44336', fg='white', font=('Arial', 11),
                 width=10).pack(side=tk.LEFT, padx=5)

    def edit_ride_dialog(self, pass_type, current_description):
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Edit {pass_type}")
        dialog.geometry("600x500")
        dialog.configure(bg='white')

        # for main frame
        main_frame = tk.Frame(dialog, bg='white', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # for description
        tk.Label(main_frame, text="Description:", font=('Arial', 11, 'bold'), 
                bg='white').pack(anchor='w', pady=(0, 5))
        description_text = tk.Text(main_frame, font=('Arial', 11), height=15)
        description_text.insert("1.0", current_description)
        description_text.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        def save_changes():
            new_description = description_text.get("1.0", tk.END).strip()

            if not new_description:
                messagebox.showwarning("Invalid Input", "Description cannot be empty.")
                return

            try:
                conn = sqlite3.connect('funpass.db')
                cursor = conn.cursor()
                cursor.execute('UPDATE rides SET description = ? WHERE pass_type = ?',
                             (new_description, pass_type))
                conn.commit()
                conn.close()
                dialog.destroy()
                self.show_rides()  # Refresh the rides page
                messagebox.showinfo("Success", "Description updated successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {str(e)}")

        # for buttons frame
        btn_frame = tk.Frame(main_frame, bg='white')
        btn_frame.pack(pady=20)

        tk.Button(btn_frame, text="Save", command=save_changes,
                 bg='#4CAF50', fg='white', font=('Arial', 11),
                 width=10).pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame, text="Cancel", command=dialog.destroy,
                 bg='#f44336', fg='white', font=('Arial', 11),
                 width=10).pack(side=tk.LEFT, padx=5)

    def delete_ride(self, pass_type):
        if messagebox.askyesno("Confirm Delete", 
                              f"Are you sure you want to delete {pass_type}?"):
            try:
                conn = sqlite3.connect('funpass.db')
                cursor = conn.cursor()
                cursor.execute('DELETE FROM rides WHERE pass_type = ?', (pass_type,))
                conn.commit()
                conn.close()
                self.show_rides()  
                messagebox.showinfo("Success", "Pass type deleted successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def show_employee_management(self):
        self.clear_content()
        
        emp_title = tk.Label(self.content_frame, text="Employee Management", font=('Arial', 16, 'bold'), bg='white', anchor='w')
        emp_title.pack(pady=(10, 0), padx=20, anchor='w')
        emp_subtitle = tk.Label(self.content_frame, text="View, Add, Edit, and Delete Employees", font=('Arial', 12), fg='#6b7280', bg='white', anchor='w')
        emp_subtitle.pack(pady=(0, 10), padx=20, anchor='w')

        # Controls frame
        controls_frame = tk.Frame(self.content_frame, bg='white')
        controls_frame.pack(fill=tk.X, pady=10)

        # Search and sort beside each other
        search_sort_frame = tk.Frame(controls_frame, bg='white')
        search_sort_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(search_sort_frame, text="Search:", bg='white').pack(side=tk.LEFT, padx=5)
        self.emp_search_var = tk.StringVar()
        self.emp_search_var.trace('w', self.search_employees)
        search_entry = tk.Entry(search_sort_frame, textvariable=self.emp_search_var, font=('Arial', 11), width=40)
        search_entry.pack(side=tk.LEFT, padx=5)
        tk.Label(search_sort_frame, text="Sort by:", bg='white').pack(side=tk.LEFT, padx=5)
        sort_options = ttk.Combobox(search_sort_frame, values=["Name (A-Z)", "Name (Z-A)", "Username (A-Z)", "Username (Z-A)"])
        sort_options.pack(side=tk.LEFT, padx=5)
        sort_options.set("Name (A-Z)")
        sort_options.bind('<<ComboboxSelected>>', lambda e: self.sort_employees(sort_options.get()))

        # Buttons frame
        buttons_frame = tk.Frame(controls_frame, bg='white')
        buttons_frame.pack(side=tk.RIGHT)

        # Add button
        add_btn = tk.Button(buttons_frame, text="Add Employee", 
                          command=lambda: self.show_employee_dialog(mode="add"),
                          bg='#4CAF50', fg='white')
        add_btn.pack(side=tk.LEFT, padx=5)

        # Edit button
        edit_btn = tk.Button(buttons_frame, text="Edit Employee", 
                           command=lambda: self.show_employee_dialog(mode="edit"),
                           bg='#2196F3', fg='white')
        edit_btn.pack(side=tk.LEFT, padx=5)

        # Delete button
        delete_btn = tk.Button(buttons_frame, text="Delete Employee", 
                             command=self.delete_employee,
                             bg='#f44336', fg='white')
        delete_btn.pack(side=tk.LEFT, padx=5)

        # Create employee table
        columns = ('ID', 'Name', 'Username', 'Password', 
                  'Express Alloc', 'Junior Alloc', 'Regular Alloc', 
                  'Student Alloc', 'PWD Alloc', 'Senior Alloc')
        self.emp_tree = ttk.Treeview(self.content_frame, columns=columns, 
                                    show='headings')
        
        # Configure columns
        self.emp_tree.heading('ID', text='ID')
        self.emp_tree.column('ID', width=50, anchor='center')
        
        self.emp_tree.heading('Name', text='Name')
        self.emp_tree.column('Name', width=150, anchor='w')
        
        self.emp_tree.heading('Username', text='Username')
        self.emp_tree.column('Username', width=100, anchor='w')
        
        self.emp_tree.heading('Password', text='Password')
        self.emp_tree.column('Password', width=100, anchor='w')
        
        # Configure allocation columns with centered text
        alloc_columns = [
            ('Express Alloc', 'Express'), ('Junior Alloc', 'Junior'),
            ('Regular Alloc', 'Regular'), ('Student Alloc', 'Student'),
            ('PWD Alloc', 'PWD'), ('Senior Alloc', 'Senior')
        ]
        
        for col, header in alloc_columns:
            self.emp_tree.heading(col, text=f'{header}\nAllocation')
            self.emp_tree.column(col, width=80, anchor='center')

        self.emp_tree.pack(fill=tk.BOTH, expand=True, pady=10)

        # Create scrollbar
        scrollbar = ttk.Scrollbar(self.content_frame, orient=tk.VERTICAL, 
                                command=self.emp_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.emp_tree.configure(yscrollcommand=scrollbar.set)

        # Load employee data
        self.load_employees()

    def show_employee_dialog(self, mode="add", event=None):
        if mode == "edit":
            selected_items = self.emp_tree.selection()
            if not selected_items:
                messagebox.showwarning("No Selection", "Please select an employee to edit.")
                return
            values = self.emp_tree.item(selected_items[0])['values']

        dialog = tk.Toplevel(self.root)
        dialog.title("Add Employee" if mode == "add" else "Edit Employee")
        dialog.geometry("500x750")  # Made taller to accommodate the new fields
        dialog.configure(bg='white')

        # to create main frame
        main_frame = tk.Frame(dialog, bg='white', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Basic info section
        basic_frame = tk.LabelFrame(main_frame, text="Basic Information", bg='white', pady=10, padx=10)
        basic_frame.pack(fill=tk.X, pady=(0, 20))

        # Basic fields
        basic_fields = [
            ('Name:', 'name'),
            ('Username:', 'username'),
            ('Password:', 'password'),
        ]

        basic_entries = {}
        for label_text, field_name in basic_fields:
            field_frame = tk.Frame(basic_frame, bg='white')
            field_frame.pack(fill=tk.X, pady=5)
            label = tk.Label(field_frame, text=label_text, bg='white', font=('Arial', 11), width=12, anchor='e')
            label.pack(side=tk.LEFT, padx=(0, 10))
            entry = tk.Entry(field_frame, font=('Arial', 11), width=30)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            basic_entries[field_name] = entry

        # Ticket allocation section
        alloc_frame = tk.LabelFrame(main_frame, text="Ticket Allocation", bg='white', pady=10, padx=10)
        alloc_frame.pack(fill=tk.X)

        # Ticket allocation fields
        alloc_fields = [
            ('Express Pass:', 'express'),
            ('Junior Pass:', 'junior'),
            ('Regular Pass:', 'regular'),
            ('Student Pass:', 'student'),
            ('PWD Pass:', 'pwd'),
            ('Senior Pass:', 'senior')
        ]

        alloc_entries = {}
        for label_text, field_name in alloc_fields:
            field_frame = tk.Frame(alloc_frame, bg='white')
            field_frame.pack(fill=tk.X, pady=5)
            label = tk.Label(field_frame, text=label_text, bg='white', font=('Arial', 11), width=12, anchor='e')
            label.pack(side=tk.LEFT, padx=(0, 10))
            
            # Create spinbox for ticket quantity
            spinbox = tk.Spinbox(field_frame, from_=0, to=1000, width=10, font=('Arial', 11))
            spinbox.pack(side=tk.LEFT)
            alloc_entries[field_name] = spinbox

        # Set values if editing
        if mode == "edit":
            basic_entries['name'].insert(0, values[1])
            basic_entries['username'].insert(0, values[2])
            basic_entries['password'].insert(0, values[3])
            
            # Set allocation values
            alloc_entries['express'].delete(0, tk.END)
            alloc_entries['express'].insert(0, values[4])
            alloc_entries['junior'].delete(0, tk.END)
            alloc_entries['junior'].insert(0, values[5])
            alloc_entries['regular'].delete(0, tk.END)
            alloc_entries['regular'].insert(0, values[6])
            alloc_entries['student'].delete(0, tk.END)
            alloc_entries['student'].insert(0, values[7])
            alloc_entries['pwd'].delete(0, tk.END)
            alloc_entries['pwd'].insert(0, values[8])
            alloc_entries['senior'].delete(0, tk.END)
            alloc_entries['senior'].insert(0, values[9])

        def save_employee():
            # Get values from entries
            employee_data = {
                'name': basic_entries['name'].get().strip(),
                'username': basic_entries['username'].get().strip(),
                'password': basic_entries['password'].get().strip(),
                'express': int(alloc_entries['express'].get()),
                'junior': int(alloc_entries['junior'].get()),
                'regular': int(alloc_entries['regular'].get()),
                'student': int(alloc_entries['student'].get()),
                'pwd': int(alloc_entries['pwd'].get()),
                'senior': int(alloc_entries['senior'].get())
            }

            # Validate inputs
            if not all([employee_data['name'], employee_data['username'], employee_data['password']]):
                messagebox.showerror("Error", "Name, username and password are required!")
                return
                
            # Validate ticket allocations
            for field in ['express', 'junior', 'regular', 'student', 'pwd', 'senior']:
                if not str(employee_data[field]).isdigit() or int(employee_data[field]) < 0:
                    messagebox.showerror("Error", f"Invalid ticket quantity for {field} pass!")
                    return

            try:
                conn = sqlite3.connect('funpass.db')
                cursor = conn.cursor()
                
                if mode == "add":
                    cursor.execute('''
                        INSERT INTO employees (
                            name, username, password, express_pass, junior_pass,
                            regular_pass, student_pass, pwd_pass, senior_citizen_pass
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        employee_data['name'], employee_data['username'],
                        employee_data['password'], employee_data['express'],
                        employee_data['junior'], employee_data['regular'],
                        employee_data['student'], employee_data['pwd'],
                        employee_data['senior']
                    ))
                else:  # edit mode
                    cursor.execute('''
                        UPDATE employees SET
                            name=?, username=?, password=?, express_pass=?,
                            junior_pass=?, regular_pass=?, student_pass=?,
                            pwd_pass=?, senior_citizen_pass=?
                        WHERE employee_id=?
                    ''', (
                        employee_data['name'], employee_data['username'],
                        employee_data['password'], employee_data['express'],
                        employee_data['junior'], employee_data['regular'],
                        employee_data['student'], employee_data['pwd'],
                        employee_data['senior'], values[0]
                    ))

                conn.commit()
                messagebox.showinfo("Success", 
                                  "Employee saved successfully!")
                dialog.destroy()
                self.load_employees()  
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Username already exists!")
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Database error: {str(e)}")
            finally:
                conn.close()

        # Create buttons frame
        btn_frame = tk.Frame(main_frame, bg='white')
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="Save", command=save_employee,
                 bg='#4CAF50', fg='white', font=('Arial', 11)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Cancel", command=dialog.destroy,
                 bg='#f44336', fg='white', font=('Arial', 11)).pack(side=tk.LEFT, padx=5)

    def delete_employee(self):
        selected_items = self.emp_tree.selection()
        if not selected_items:
            messagebox.showwarning("No Selection", "Please select an employee to delete.")
            return

        if messagebox.askyesno("Confirm Delete", 
                             "Are you sure you want to delete this employee?"):
            employee_id = self.emp_tree.item(selected_items[0])['values'][0]

            conn = sqlite3.connect('funpass.db')
            cursor = conn.cursor()
            try:
                cursor.execute('DELETE FROM employees WHERE employee_id = ?', 
                             (employee_id,))
                conn.commit()
                self.emp_tree.delete(selected_items[0])
                messagebox.showinfo("Success", "Employee deleted successfully!")
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Database error: {str(e)}")
            finally:
                conn.close()

    def load_employees(self):
        # to clear existing items
        for item in self.emp_tree.get_children():
            self.emp_tree.delete(item)
            
        # to load from database
        conn = sqlite3.connect('funpass.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM employees')
        employees = cursor.fetchall()
        conn.close()
        
            # to insert into treeview
        for emp in employees:
            self.emp_tree.insert('', tk.END, values=emp)

    def show_customers(self):
        self.clear_content()
        customer_title = tk.Label(self.content_frame, text="Customers", font=('Arial', 16, 'bold'), bg='white', anchor='w')
        customer_title.pack(pady=(10, 0), padx=20, anchor='w')
        customer_subtitle = tk.Label(self.content_frame, text="View All Customers and Ticket Sales", font=('Arial', 12), fg='#6b7280', bg='white', anchor='w')
        customer_subtitle.pack(pady=(0, 10), padx=20, anchor='w')

        controls_frame = tk.Frame(self.content_frame, bg='white')
        controls_frame.pack(fill=tk.X, pady=10)

        # Search and sort beside each other
        search_sort_frame = tk.Frame(controls_frame, bg='white')
        search_sort_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(search_sort_frame, text="Search:", bg='white').pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.search_customers)
        search_entry = tk.Entry(search_sort_frame, textvariable=self.search_var, font=('Arial', 11), width=40)
        search_entry.pack(side=tk.LEFT, padx=5)
        tk.Label(search_sort_frame, text="Sort by:", bg='white').pack(side=tk.LEFT, padx=5)
        sort_options = ttk.Combobox(search_sort_frame, values=["Name (A-Z)", "Name (Z-A)", "Date (Newest)", "Date (Oldest)"])
        sort_options.pack(side=tk.LEFT, padx=5)
        sort_options.set("Name (A-Z)")
        sort_options.bind('<<ComboboxSelected>>', lambda e: self.sort_customers(sort_options.get()))

        # Add buttons frame
        buttons_frame = tk.Frame(controls_frame, bg='white')
        buttons_frame.pack(side=tk.RIGHT, padx=10)

        # Add delete button
        delete_btn = tk.Button(buttons_frame, text="Delete", 
                             command=self.delete_customer,
                             bg='#f44336', fg='white')
        delete_btn.pack(side=tk.LEFT, padx=5)

        columns = ('Ticket ID', 'Name', 'Email', 'Quantity', 'Amount', 'Booked Date', 'Purchased Date', 'Employee')
        self.customers_tree = ttk.Treeview(self.content_frame, columns=columns, show='headings')
        for col in columns:
            self.customers_tree.heading(col, text=col)
            self.customers_tree.column(col, width=120)
        self.customers_tree.pack(fill=tk.BOTH, expand=True, pady=10)
        scrollbar = ttk.Scrollbar(self.content_frame, orient=tk.VERTICAL, command=self.customers_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.customers_tree.configure(yscrollcommand=scrollbar.set)
        self.load_customers_data()

    def search_customers(self, *args):
        search_text = self.search_var.get().lower()
        for item in self.customers_tree.get_children():
            self.customers_tree.delete(item)
        conn = sqlite3.connect('funpass.db')
        cursor = conn.cursor()
        cursor.execute('''SELECT c.ticket_id, c.name, c.email, c.quantity, c.amount, 
                    strftime('%m/%d/%Y', c.booked_date) as booked_date, 
                    strftime('%m/%d/%Y', c.purchased_date) as purchased_date, 
                    IFNULL(e.name, '') as employee_name 
                    FROM customers c 
                    LEFT JOIN employees e ON c.employee_id = e.employee_id''')
        customers = cursor.fetchall()
        conn.close()
        for customer in customers:
            if any(search_text in str(value).lower() for value in customer):
                self.customers_tree.insert('', tk.END, values=customer)

    def sort_customers(self, sort_option):
        items = []
        for item in self.customers_tree.get_children():
            values = self.customers_tree.item(item)['values']
            items.append(values)
        if sort_option == "Name (A-Z)":
            items.sort(key=lambda x: x[1])
        elif sort_option == "Name (Z-A)":
            items.sort(key=lambda x: x[1], reverse=True)
        elif sort_option == "Date (Newest)":
            items.sort(key=lambda x: x[6], reverse=True)
        elif sort_option == "Date (Oldest)":
            items.sort(key=lambda x: x[6])
        for item in self.customers_tree.get_children():
            self.customers_tree.delete(item)
        for item in items:
            self.customers_tree.insert('', tk.END, values=item)

    def load_customers_data(self):
        for item in self.customers_tree.get_children():
            self.customers_tree.delete(item)
        conn = sqlite3.connect('funpass.db')
        cursor = conn.cursor()
        cursor.execute('''SELECT c.ticket_id, c.name, c.email, c.quantity, c.amount, 
                    strftime('%m/%d/%Y', c.booked_date) as booked_date, 
                    strftime('%m/%d/%Y', c.purchased_date) as purchased_date, 
                    IFNULL(e.name, '') as employee_name 
                    FROM customers c 
                    LEFT JOIN employees e ON c.employee_id = e.employee_id''')
        customers = cursor.fetchall()
        conn.close()
        for customer in customers:
            self.customers_tree.insert('', tk.END, values=customer)

    def show_cancellations(self):
        self.clear_content()
        
        # to add cancellations and refunds title and subtitle
        cancel_title = tk.Label(self.content_frame, text="Cancellations and Refunds", font=('Arial', 16, 'bold'), bg='white', anchor='w')
        cancel_title.pack(pady=(10, 0), padx=20, anchor='w')
        cancel_subtitle = tk.Label(self.content_frame, text="View and Manage Customers Submitted Refund Requests", font=('Arial', 12), fg='#6b7280', bg='white', anchor='w')
        cancel_subtitle.pack(pady=(0, 10), padx=20, anchor='w')

        # to create top controls frame
        controls_frame = tk.Frame(self.content_frame, bg='white')
        controls_frame.pack(fill=tk.X, pady=10)

        # to add search functionality
        search_frame = tk.Frame(controls_frame, bg='white')
        search_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Label(search_frame, text="Search:", bg='white').pack(side=tk.LEFT, padx=5)
        self.cancel_search_var = tk.StringVar()
        self.cancel_search_var.trace('w', self.search_cancellations)
        search_entry = tk.Entry(search_frame, textvariable=self.cancel_search_var, 
                              font=('Arial', 11), width=30)
        search_entry.pack(side=tk.LEFT, padx=5)
        tk.Label(search_frame, text="Sort by:", bg='white').pack(side=tk.LEFT, padx=5)
        sort_options = ttk.Combobox(search_frame, values=["Name (A-Z)", "Name (Z-A)", "Date (Newest)", "Date (Oldest)", "Status (A-Z)", "Status (Z-A)"])
        sort_options.pack(side=tk.LEFT, padx=5)
        sort_options.set("Name (A-Z)")
        sort_options.bind('<<ComboboxSelected>>', lambda e: self.sort_cancellations(sort_options.get()))

        # to create buttons frame
        buttons_frame = tk.Frame(controls_frame, bg='white')
        buttons_frame.pack(side=tk.RIGHT, padx=10)

        # to create edit status button
        edit_btn = tk.Button(buttons_frame, text="Edit Status", 
                           command=self.edit_cancellation_status,
                           bg='#4CAF50', fg='white')
        edit_btn.pack(side=tk.LEFT, padx=5)

        # to create delete button
        delete_btn = tk.Button(buttons_frame, text="Delete", 
                             command=self.delete_cancellation,
                             bg='#f44336', fg='white')
        delete_btn.pack(side=tk.LEFT, padx=5)

        # to create cancellations table
        columns = ('Ticket ID', 'Name', 'Email', 'Reason', 'Quantity', 'Amount', 
                  'Booked Date', 'Purchased Date', 'Status')
        self.cancellations_tree = ttk.Treeview(self.content_frame, columns=columns, 
                                              show='headings')
        
        # Configure columns with custom widths and left alignment
        column_widths = {
            'Ticket ID': 100,
            'Name': 150,
            'Email': 200,
            'Reason': 200,
            'Quantity': 80,
            'Amount': 100,
            'Booked Date': 120,
            'Purchased Date': 120,
            'Status': 100
        }
        
        for col in columns:
            self.cancellations_tree.heading(col, text=col)
            width = column_widths.get(col, 120)  # default to 120 if not specified
            self.cancellations_tree.column(col, width=width, anchor='w')

        self.cancellations_tree.pack(fill=tk.BOTH, expand=True, pady=10)

        # to add scrollbar
        scrollbar = ttk.Scrollbar(self.content_frame, orient=tk.VERTICAL, 
                                command=self.cancellations_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.cancellations_tree.configure(yscrollcommand=scrollbar.set)

        # to load initial data
        self.load_cancellations_data()

    def edit_cancellation_status(self):
        selected_item = self.cancellations_tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a cancellation to edit.")
            return

        # to get current values
        current_values = self.cancellations_tree.item(selected_item[0])['values']
        
        # to create edit window
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Edit Cancellation Status")
        edit_window.geometry("400x300")
        edit_window.configure(bg='white')

        # to create edit frame
        edit_frame = tk.Frame(edit_window, bg='white', padx=20, pady=20)
        edit_frame.pack(fill=tk.BOTH, expand=True)

        # to show current status
        tk.Label(edit_frame, text="Current Status:", font=('Arial', 11, 'bold'), 
                bg='white').pack(pady=5)
        tk.Label(edit_frame, text=current_values[8], font=('Arial', 11), 
                bg='white').pack(pady=5)

        # to create new status selection
        tk.Label(edit_frame, text="New Status:", font=('Arial', 11, 'bold'), 
                bg='white').pack(pady=10)
        status_var = tk.StringVar(value=current_values[8])
        status_combo = ttk.Combobox(edit_frame, textvariable=status_var,
                                  values=["Pending", "Approved", "Rejected"])
        status_combo.pack(pady=5)

        def save_status():
            new_status = status_var.get()
            if new_status != current_values[8]:
                # to update database
                conn = sqlite3.connect('funpass.db')
                cursor = conn.cursor()
                cursor.execute('UPDATE cancellations SET status = ? WHERE ticket_id = ?',
                             (new_status, current_values[0]))
                conn.commit()
                conn.close()

                # to update treeview
                new_values = list(current_values)
                new_values[8] = new_status
                self.cancellations_tree.item(selected_item[0], values=new_values)
                
                messagebox.showinfo("Success", "Status updated successfully!")
                edit_window.destroy()

        # to create buttons
        buttons_frame = tk.Frame(edit_frame, bg='white')
        buttons_frame.pack(pady=20)
        
        tk.Button(buttons_frame, text="Save", command=save_status,
                 bg='#4CAF50', fg='white', font=('Arial', 11)).pack(side=tk.LEFT, padx=5)
        tk.Button(buttons_frame, text="Cancel", command=edit_window.destroy,
                 bg='#f44336', fg='white', font=('Arial', 11)).pack(side=tk.LEFT, padx=5)

    def delete_cancellation(self):
        selected_item = self.cancellations_tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a cancellation to delete.")
            return

        if messagebox.askyesno("Confirm Delete", 
                             "Are you sure you want to delete this cancellation record?"):
            # to get ticket ID
            ticket_id = self.cancellations_tree.item(selected_item[0])['values'][0]

            # to delete from database
            conn = sqlite3.connect('funpass.db')
            cursor = conn.cursor()
            cursor.execute('DELETE FROM cancellations WHERE ticket_id = ?', (ticket_id,))
            conn.commit()
            conn.close()

            # to remove from treeview
            self.cancellations_tree.delete(selected_item[0])
            messagebox.showinfo("Success", "Cancellation record deleted successfully!")

    def search_cancellations(self, *args):
        search_text = self.cancel_search_var.get().lower()

        # Clear current display
        for item in self.cancellations_tree.get_children():
            self.cancellations_tree.delete(item)

        # Get all cancellations from database
        conn = sqlite3.connect('funpass.db')
        cursor = conn.cursor()
        cursor.execute('''

        SELECT 
            ticket_id, name, email, reasons, quantity, amount,
            strftime('%m/%d/%Y', booked_date) as booked_date, 
            strftime('%m/%d/%Y', purchased_date) as purchased_date,
            status
        FROM cancellations
    ''')
        cancellations = cursor.fetchall()
        conn.close()

        # Filter and display matching cancellations
        for cancellation in cancellations:
            # Search in all relevant fields (ticket_id, name, email, status)
            searchable_fields = [
                str(cancellation[0]),  # ticket_id
                str(cancellation[1]),  # name
                str(cancellation[2]),  # email
                str(cancellation[8])   # status
            ]
            if any(search_text in field.lower() for field in searchable_fields):
                self.cancellations_tree.insert('', tk.END, values=cancellation)

    def sort_cancellations(self, sort_option):
        items = []
        for item in self.cancellations_tree.get_children():
            values = self.cancellations_tree.item(item)['values']
            items.append(values)
        if sort_option == "Name (A-Z)":
            items.sort(key=lambda x: x[1])
        elif sort_option == "Name (Z-A)":
            items.sort(key=lambda x: x[1], reverse=True)
        elif sort_option == "Date (Newest)":
            items.sort(key=lambda x: x[7], reverse=True)
        elif sort_option == "Date (Oldest)":
            items.sort(key=lambda x: x[7])
        elif sort_option == "Status (A-Z)":
            items.sort(key=lambda x: x[8])
        elif sort_option == "Status (Z-A)":
            items.sort(key=lambda x: x[8], reverse=True)
        for item in self.cancellations_tree.get_children():
            self.cancellations_tree.delete(item)
        for item in items:
            self.cancellations_tree.insert('', tk.END, values=item)

    def load_cancellations_data(self):
        # to clear existing items
        for item in self.cancellations_tree.get_children():
            self.cancellations_tree.delete(item)
            
        # to load from database
        conn = sqlite3.connect('funpass.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                ticket_id, name, email, reasons, quantity, amount,
                strftime('%m/%d/%Y', booked_date) as booked_date, 
                strftime('%m/%d/%Y', purchased_date) as purchased_date,
                status
            FROM cancellations
            ORDER BY id DESC
        ''')
        cancellations = cursor.fetchall()
        conn.close()
        
        # to insert into treeview
        for cancellation in cancellations:
            self.cancellations_tree.insert('', tk.END, values=cancellation)

    def show_pricing(self):
        self.clear_content()
        
        # Add pass type pricing title and subtitle
        pricing_title = tk.Label(self.content_frame, text="Pass Type Pricing", font=('Arial', 16, 'bold'), bg='white', anchor='w')
        pricing_title.pack(pady=(10, 0), padx=20, anchor='w')
        
        self.price_update_label = tk.Label(self.content_frame, text="", font=('Arial', 10), fg='#4CAF50', bg='white', anchor='w')
        self.price_update_label.pack(pady=(5, 0), padx=20, anchor='w')
        
        pricing_subtitle = tk.Label(self.content_frame, text="View and Manage Ticketing Pricing", font=('Arial', 12), fg='#6b7280', bg='white', anchor='w')
        pricing_subtitle.pack(pady=(0, 10), padx=20, anchor='w')

        # Create main frame for pricing
        main_frame = tk.Frame(self.content_frame, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=50, pady=20)

        # Get current prices from database
        conn = sqlite3.connect('funpass.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM pricing')
        prices = cursor.fetchall()
        conn.close()

        # Store entry widgets
        self.price_entries = {}

        # Create price editing interface
        for pass_type, current_price in prices:
            # Create frame for each row
            row = tk.Frame(main_frame, bg='white', name=f"price_row_{pass_type.replace(' ', '_').lower()}")
            row.pack(fill=tk.X, pady=10)

            # Create pass type label (left-aligned)
            label = tk.Label(row, text=pass_type, font=('Arial', 12), bg='white',
                           width=20, anchor='w')
            label.pack(side=tk.LEFT, padx=(20, 10))

            # Create price entry with currency symbol
            price_frame = tk.Frame(row, bg='white')
            price_frame.pack(side=tk.LEFT)

            currency_label = tk.Label(price_frame, text="₱", font=('Arial', 12), bg='white')
            currency_label.pack(side=tk.LEFT, padx=(0, 5))

            # Create StringVar with initial formatted price
            price_var = tk.StringVar(value=f"{float(current_price):.2f}")
            
            # Add validation to only allow numbers and decimal point
            def validate_price(action, value_if_allowed):
                if action == '1':  # Insert
                    if value_if_allowed == "":
                        return True
                    try:
                        # Remove commas for validation
                        cleaned_value = value_if_allowed.replace(',', '')
                        # Allow numbers, single decimal point, and optional negative sign
                        if cleaned_value.count('.') <= 1 and cleaned_value.replace('.', '').replace('-', '', 1).isdigit():
                            # Don't allow just a decimal point or negative sign
                            if cleaned_value not in ['.', '-']:
                                return True
                    except ValueError:
                        pass
                    return False
                return True

            entry = tk.Entry(price_frame, textvariable=price_var, 
                           font=('Arial', 12), width=10,
                           justify='right',
                           name=f"price_entry_{pass_type.replace(' ', '_').lower()}")
            entry.pack(side=tk.LEFT)
            
            self.price_entries[pass_type] = price_var
            
            vcmd = (entry.register(validate_price), '%d', '%P')
            entry.configure(validate="key", validatecommand=vcmd)

            # Add immediate feedback on invalid input
            def on_invalid_input(event):
                widget = event.widget
                if widget.get():
                    try:
                        float(widget.get().replace(',', ''))
                        widget.config(fg='black')
                    except ValueError:
                        widget.config(fg='red')
            
            entry.bind('<KeyRelease>', on_invalid_input)

        # Create buttons frame
        btn_frame = tk.Frame(self.content_frame, bg='white')
        btn_frame.pack(pady=20)

        # Create save button
        save_btn = tk.Button(btn_frame, text="Save Changes", 
                           command=self.save_prices,
                           bg='#4CAF50', fg='white', 
                           font=('Arial', 11, 'bold'),
                           width=15, height=2)
        save_btn.pack(side=tk.LEFT, padx=10)

        # Create reset button
        reset_btn = tk.Button(btn_frame, text="Reset", 
                            command=self.reset_prices,
                            bg='#f44336', fg='white', 
                            font=('Arial', 11, 'bold'),
                            width=15, height=2)
        reset_btn.pack(side=tk.LEFT, padx=10)

        # Show last update time
        self.price_update_label.config(text=f"Last updated: {time.strftime('%m/%d/%Y %H:%M:%S')}")

    def save_prices(self):
        try:
            # Validate that all prices are valid numbers and store them
            new_prices = {}
            for pass_type, price_var in self.price_entries.items():
                try:
                    # Remove any commas and spaces from the price string
                    price_str = price_var.get().replace(',', '').replace(' ', '')
                    price = float(price_str)
                    if price < 0:
                        raise ValueError(f"Price for {pass_type} cannot be negative")
                    new_prices[pass_type] = price
                except ValueError as e:
                    messagebox.showerror("Invalid Input", str(e))
                    return False

            # Start database transaction
            conn = sqlite3.connect('funpass.db')
            try:
                cursor = conn.cursor()
                # Begin transaction
                cursor.execute('BEGIN')

                for pass_type, price in new_prices.items():
                    # Update price in database
                    cursor.execute('UPDATE pricing SET price = ? WHERE pass_type = ?',
                                 (price, pass_type))
                    # Update the entry display with the formatted price
                    self.price_entries[pass_type].set(f"{price:.2f}")
                
                # Commit transaction
                conn.commit()

                # Generate price update event
                if hasattr(self, 'root') and self.root:
                    print("Generating price update event")  # Debug print
                    self.root.event_generate('<<PriceUpdate>>')
                    print("Price update event generated successfully")  # Debug print
                
                messagebox.showinfo("Success", "Prices updated successfully!")
                return True

            except sqlite3.Error as e:
                # Rollback on error
                conn.rollback()
                messagebox.showerror("Database Error", f"An error occurred: {str(e)}")
                return False
            finally:
                conn.close()

        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")
            return False

    def reset_prices(self):
        if messagebox.askyesno("Confirm Reset", 
                             "Are you sure you want to reset to default prices?"):
            default_prices = {
                'Express Pass': 2300.00,
                'Junior Pass': 900.00,
                'Regular Pass': 1300.00,
                'Student Pass': 1300.00,
                'Senior Citizen Pass': 900.00,
                'PWD Pass': 900.00
            }

            # Update entry fields
            for pass_type, price in default_prices.items():
                if pass_type in self.price_entries:
                    self.price_entries[pass_type].set(f"{price:.2f}")

            # Save to database
            try:
                conn = sqlite3.connect('funpass.db')
                cursor = conn.cursor()
                
                for pass_type, price in default_prices.items():
                    cursor.execute('UPDATE pricing SET price = ? WHERE pass_type = ?',
                                 (price, pass_type))
                
                conn.commit()
                conn.close()
                
                # Notify employee dashboard to refresh prices
                self.notify_price_update()
                
                messagebox.showinfo("Success", "Prices reset to default values!")
            except sqlite3.Error as e:
                messagebox.showerror("Database Error", f"An error occurred: {str(e)}")

    def notify_price_update(self):
        # Call refresh prices on all employee dashboards
        if hasattr(self, 'root') and self.root:
            self.root.event_generate('<<PriceUpdate>>')

    def logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.root.destroy()
            from login import show_login
            show_login()

    def search_employees(self, *args):
        search_text = self.emp_search_var.get().lower()
        
        # to clear current display
        for item in self.emp_tree.get_children():
            self.emp_tree.delete(item)
            
        # to get all employees from database   
        conn = sqlite3.connect('funpass.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM employees')
        employees = cursor.fetchall()
        conn.close()
        
        # to filter and display matching employees
        for employee in employees:
            # to search in all fields
            if any(search_text in str(value).lower() for value in employee):
                self.emp_tree.insert('', tk.END, values=employee)

    def sort_employees(self, sort_option):
        # to get all items
        items = []
        for item in self.emp_tree.get_children():
            values = self.emp_tree.item(item)['values']
            items.append(values)

        # to sort based on selected option
        if sort_option == "Name (A-Z)":
            items.sort(key=lambda x: x[1])  # to sort by name ascending
        elif sort_option == "Name (Z-A)":
            items.sort(key=lambda x: x[1], reverse=True)  # to sort by name descending
        elif sort_option == "Username (A-Z)":
            items.sort(key=lambda x: x[2])  # to sort by username ascending
        elif sort_option == "Username (Z-A)":
            items.sort(key=lambda x: x[2], reverse=True)  # to sort by username descending

        # to clear and reload table
        for item in self.emp_tree.get_children():
            self.emp_tree.delete(item)
        
        for item in items:
            self.emp_tree.insert('', tk.END, values=item)

    def delete_customer(self):
        selected_item = self.customers_tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a customer record to delete.")
            return

        if messagebox.askyesno("Confirm Delete", 
                             "Are you sure you want to delete this customer record?\nThis action cannot be undone."):

            # Get ticket ID from selected item
            ticket_id = self.customers_tree.item(selected_item[0])['values'][0]

            try:
                conn = sqlite3.connect('funpass.db')
                cursor = conn.cursor()
                
                # Delete the customer record
                cursor.execute('DELETE FROM customers WHERE ticket_id = ?', (ticket_id,))
                
                # Commit changes and close connection
                conn.commit()
                conn.close()

                # Remove from treeview
                self.customers_tree.delete(selected_item[0])
                
                messagebox.showinfo("Success", "Customer record deleted successfully!")
            
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"An error occurred: {str(e)}")
                
            except Exception as e:
                messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    create_database()  # to initialize the database
    root = tk.Tk()
    app = AdminDashboard(root)
    root.mainloop()
