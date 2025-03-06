import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk
from flask import Flask, request, jsonify
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import requests

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

@app.route("/api/summary", methods=["GET"])
def get_summary():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "User ID required"}), 400
    
    conn = sqlite3.connect("budget.db")
    c = conn.cursor()
    
    c.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type = 'income'", (user_id,))
    total_income = c.fetchone()[0] or 0
    
    c.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type = 'expense'", (user_id,))
    total_expense = c.fetchone()[0] or 0
    
    c.execute("SELECT type, amount, description FROM transactions WHERE user_id = ? ORDER BY id DESC LIMIT 5", (user_id,))
    recent_transactions = c.fetchall()
    
    conn.close()
    
    return jsonify({
        "total_income": total_income,
        "total_expense": total_expense,
        "recent_transactions": recent_transactions
    })

# GUI Application
class BudgetApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Budget App")
        self.root.geometry("800x600")
        self.root.configure(bg='#f0f0f0')
        
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TButton', font=('Arial', 12), padding=5)
        self.style.configure('Treeview', rowheight=30)
        self.style.map('Treeview', background=[('selected', '#007bff')])
        
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.create_login_widgets()

    def create_login_widgets(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        login_frame = tk.Frame(self.root, bg='#f0f0f0')
        login_frame.pack(expand=True, fill=tk.BOTH, padx=50, pady=50)
        
        tk.Label(login_frame, text="Budget App", font=('Arial', 24, 'bold'), 
                bg='#f0f0f0', fg='#333').pack(pady=20)
        
        form_frame = tk.Frame(login_frame, bg='#f0f0f0')
        form_frame.pack(pady=20)
        
        tk.Label(form_frame, text="Username", font=('Arial', 12), bg='#f0f0f0').grid(row=0, column=0, padx=10, pady=5)
        tk.Entry(form_frame, textvariable=self.username_var, font=('Arial', 12), 
                width=25).grid(row=0, column=1, padx=10, pady=5)
        
        tk.Label(form_frame, text="Password", font=('Arial', 12), bg='#f0f0f0').grid(row=1, column=0, padx=10, pady=5)
        tk.Entry(form_frame, textvariable=self.password_var, show="*", 
                font=('Arial', 12), width=25).grid(row=1, column=1, padx=10, pady=5)
        
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
        for widget in self.root.winfo_children():
            widget.destroy()
        
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
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
        
        tree_frame = tk.Frame(main_frame, bg='#f0f0f0')
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        self.transactions_tree = ttk.Treeview(tree_frame, columns=("Type", "Amount", "Description"), show="headings")
        self.transactions_tree.heading("Type", text="Type ↓", command=lambda: self.sort_treeview("Type", False))
        self.transactions_tree.heading("Amount", text="Amount ↓", command=lambda: self.sort_treeview("Amount", False))
        self.transactions_tree.heading("Description", text="Description ↓", command=lambda: self.sort_treeview("Description", False))
        self.transactions_tree.column("Type", width=100, anchor=tk.CENTER)
        self.transactions_tree.column("Amount", width=150, anchor=tk.CENTER)
        self.transactions_tree.column("Description", width=300, anchor=tk.W)
        self.transactions_tree.tag_configure('income', background='#d4edda')
        self.transactions_tree.tag_configure('expense', background='#f8d7da')
        self.transactions_tree.pack(fill=tk.BOTH, expand=True)
        
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
        
        tk.Button(main_frame, text="View Budget Analysis", command=self.show_analysis,
                 font=('Arial', 12), bg='#17a2b8', fg='white').pack(pady=10)
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
    
    def sort_treeview(self, col, reverse):
        l = [(self.transactions_tree.set(k, col), k) for k in self.transactions_tree.get_children('')]
        
        try:
            if col == "Amount":
                l.sort(key=lambda t: float(t[0]), reverse=reverse)
            else:
                l.sort(reverse=reverse)
        except:
            pass
        
        for index, (val, k) in enumerate(l):
            self.transactions_tree.move(k, '', index)
            
        self.transactions_tree.heading(col, 
            text=f"{col} {'↑' if reverse else '↓'}",
            command=lambda: self.sort_treeview(col, not reverse))

    def show_analysis(self):
        analysis_win = tk.Toplevel(self.root)
        analysis_win.title("Budget Analysis")
        analysis_win.geometry("800x600")
        
        try:
            response = requests.get(f"http://localhost:5000/api/summary?user_id={self.user_id}")
            data = response.json()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch analysis data: {str(e)}")
            return
        
        fig = plt.Figure(figsize=(8, 6), dpi=100)
        
        ax1 = fig.add_subplot(121)
        ax1.set_title("Income vs Expenses")
        labels = ['Income', 'Expenses']
        sizes = [data['total_income'], data['total_expense']]
        ax1.pie(sizes, labels=labels, autopct='%1.1f%%', colors=['#28a745', '#dc3545'])
        
        ax2 = fig.add_subplot(122)
        ax2.set_title("Recent Transactions")
        transactions = data['recent_transactions'][::-1]
        amounts = [t[1] for t in transactions]
        labels = [t[2][:15] + '...' if len(t[2]) > 15 else t[2] for t in transactions]
        colors = ['#28a745' if t[0] == 'income' else '#dc3545' for t in transactions]
        ax2.barh(labels, amounts, color=colors)
        ax2.invert_yaxis()
        
        canvas = FigureCanvasTkAgg(fig, master=analysis_win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def logout(self):
        self.user_id = None
        self.create_login_widgets()

def run_flask():
    app.run(threaded=True)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    root = tk.Tk()
    app = BudgetApp(root)
    root.mainloop()