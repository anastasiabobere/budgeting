import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk
from flask import Flask, request, jsonify

# Database Setup
def init_db():
    conn = sqlite3.connect("budget.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    type TEXT,
                    amount REAL,
                    description TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id))''')
    conn.commit()
    conn.close()

init_db()

# Flask API
app = Flask(__name__)

@app.route("/api/transactions", methods=["GET"])
def get_transactions():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "User ID required"}), 400
    conn = sqlite3.connect("budget.db")
    c = conn.cursor()
    c.execute("SELECT type, amount, description FROM transactions WHERE user_id = ?", (user_id,))
    data = c.fetchall()
    conn.close()
    return jsonify(data)

# GUI Application
class BudgetApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Budget App")
        self.root.geometry("800x600")
        self.root.configure(bg='#f0f0f0')
        
        # Configure styles
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TButton', font=('Arial', 12), padding=5)
        self.style.configure('Treeview', rowheight=30)
        self.style.map('Treeview', background=[('selected', '#007bff')])
        
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.create_login_widgets()

    def create_login_widgets(self):
        # Clear existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Login Frame
        login_frame = tk.Frame(self.root, bg='#f0f0f0')
        login_frame.pack(expand=True, fill=tk.BOTH, padx=50, pady=50)
        
        # Title
        tk.Label(login_frame, text="Budget App", font=('Arial', 24, 'bold'), 
                bg='#f0f0f0', fg='#333').pack(pady=20)
        
        # Login Form
        form_frame = tk.Frame(login_frame, bg='#f0f0f0')
        form_frame.pack(pady=20)
        
        tk.Label(form_frame, text="Username", font=('Arial', 12), bg='#f0f0f0').grid(row=0, column=0, padx=10, pady=5)
        tk.Entry(form_frame, textvariable=self.username_var, font=('Arial', 12), 
                width=25).grid(row=0, column=1, padx=10, pady=5)
        
        tk.Label(form_frame, text="Password", font=('Arial', 12), bg='#f0f0f0').grid(row=1, column=0, padx=10, pady=5)
        tk.Entry(form_frame, textvariable=self.password_var, show="*", 
                font=('Arial', 12), width=25).grid(row=1, column=1, padx=10, pady=5)
        
        # Buttons
        btn_frame = tk.Frame(login_frame, bg='#f0f0f0')
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="Register", command=self.register, 
                 font=('Arial', 12), bg='#007bff', fg='white', width=12).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Login", command=self.login, 
                 font=('Arial', 12), bg='#28a745', fg='white', width=12).pack(side=tk.LEFT, padx=10)

    def register(self):
        username = self.username_var.get()
        password = self.password_var.get()
        conn = sqlite3.connect("budget.db")
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            messagebox.showinfo("Success", "Registration Successful!")
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already exists")
        conn.close()
    
    def login(self):
        username = self.username_var.get()
        password = self.password_var.get()
        conn = sqlite3.connect("budget.db")
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            self.user_id = user[0]
            self.open_budget_window()
        else:
            messagebox.showerror("Error", "Invalid credentials")
    
    def open_budget_window(self):
        # Clear existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Main container
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Transaction Input
        input_frame = tk.Frame(main_frame, bg='#f0f0f0')
        input_frame.pack(fill=tk.X, pady=10)
        
        self.amount_var = tk.DoubleVar()
        self.desc_var = tk.StringVar()
        
        tk.Label(input_frame, text="Amount ($)", font=('Arial', 12), bg='#f0f0f0').grid(row=0, column=0, padx=5)
        tk.Entry(input_frame, textvariable=self.amount_var, font=('Arial', 12), width=15).grid(row=0, column=1, padx=5)
        
        tk.Label(input_frame, text="Description", font=('Arial', 12), bg='#f0f0f0').grid(row=0, column=2, padx=5)
        tk.Entry(input_frame, textvariable=self.desc_var, font=('Arial', 12), width=30).grid(row=0, column=3, padx=5)
        
        btn_frame = tk.Frame(input_frame, bg='#f0f0f0')
        btn_frame.grid(row=0, column=4, padx=10)
        
        tk.Button(btn_frame, text="Add Income", command=lambda: self.add_transaction("income"),
                 bg='#28a745', fg='white', font=('Arial', 12)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Add Expense", command=lambda: self.add_transaction("expense"),
                 bg='#dc3545', fg='white', font=('Arial', 12)).pack(side=tk.LEFT, padx=5)
        
        # Transactions Treeview
        tree_frame = tk.Frame(main_frame, bg='#f0f0f0')
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        self.transactions_tree = ttk.Treeview(tree_frame, columns=("Type", "Amount", "Description"), show="headings")
        self.transactions_tree.heading("Type", text="Type")
        self.transactions_tree.heading("Amount", text="Amount ($)")
        self.transactions_tree.heading("Description", text="Description")
        self.transactions_tree.column("Type", width=100, anchor=tk.CENTER)
        self.transactions_tree.column("Amount", width=150, anchor=tk.CENTER)
        self.transactions_tree.column("Description", width=300, anchor=tk.W)
        self.transactions_tree.tag_configure('income', background='#d4edda')
        self.transactions_tree.tag_configure('expense', background='#f8d7da')
        self.transactions_tree.pack(fill=tk.BOTH, expand=True)
        
        # Summary Section
        summary_frame = tk.Frame(main_frame, bg='#ffffff', bd=1, relief=tk.SOLID)
        summary_frame.pack(fill=tk.X, pady=20, padx=10)
        
        tk.Label(summary_frame, text="Total Income:", font=('Arial', 12), 
                bg='#ffffff').grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
        self.total_income_label = tk.Label(summary_frame, text="$0.00", font=('Arial', 12), bg='#ffffff')
        self.total_income_label.grid(row=0, column=1, padx=10, pady=5, sticky=tk.W)
        
        tk.Label(summary_frame, text="Total Expenses:", font=('Arial', 12), 
                bg='#ffffff').grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        self.total_expense_label = tk.Label(summary_frame, text="$0.00", font=('Arial', 12), bg='#ffffff')
        self.total_expense_label.grid(row=1, column=1, padx=10, pady=5, sticky=tk.W)
        
        tk.Label(summary_frame, text="Balance:", font=('Arial', 12, 'bold'), 
                bg='#ffffff').grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
        self.balance_label = tk.Label(summary_frame, text="$0.00", font=('Arial', 12, 'bold'), bg='#ffffff')
        self.balance_label.grid(row=2, column=1, padx=10, pady=5, sticky=tk.W)
        
        # Logout Button
        tk.Button(main_frame, text="Logout", command=self.logout, 
                 font=('Arial', 12), bg='#6c757d', fg='white').pack(pady=10)
        
        self.load_transactions()
    
    def add_transaction(self, trans_type):
        amount = self.amount_var.get()
        description = self.desc_var.get()
        if amount <= 0 or not description:
            messagebox.showerror("Error", "Please enter valid amount and description")
            return
        
        conn = sqlite3.connect("budget.db")
        c = conn.cursor()
        c.execute("INSERT INTO transactions (user_id, type, amount, description) VALUES (?, ?, ?, ?)", 
                  (self.user_id, trans_type, amount, description))
        conn.commit()
        conn.close()
        self.amount_var.set(0)
        self.desc_var.set("")
        self.load_transactions()
    
    def load_transactions(self):
        for row in self.transactions_tree.get_children():
            self.transactions_tree.delete(row)
        
        conn = sqlite3.connect("budget.db")
        c = conn.cursor()
        c.execute("SELECT type, amount, description FROM transactions WHERE user_id = ?", (self.user_id,))
        transactions = c.fetchall()
        conn.close()
        
        total_income = 0
        total_expense = 0
        for trans in transactions:
            if trans[0] == 'income':
                total_income += trans[1]
                self.transactions_tree.insert("", "end", values=trans, tags=('income',))
            else:
                total_expense += trans[1]
                self.transactions_tree.insert("", "end", values=trans, tags=('expense',))
        
        balance = total_income - total_expense
        self.total_income_label.config(text=f"${total_income:.2f}")
        self.total_expense_label.config(text=f"${total_expense:.2f}")
        self.balance_label.config(text=f"${balance:.2f}")
        self.balance_label.config(fg='#28a745' if balance >= 0 else '#dc3545')
    
    def logout(self):
        self.user_id = None
        self.create_login_widgets()

if __name__ == "__main__":
    root = tk.Tk()
    app = BudgetApp(root)
    root.mainloop()