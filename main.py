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
        self.root.geometry("400x300")
        
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        
        tk.Label(root, text="Username", font=("Arial", 12)).pack()
        tk.Entry(root, textvariable=self.username_var, font=("Arial", 12)).pack()
        tk.Label(root, text="Password", font=("Arial", 12)).pack()
        tk.Entry(root, textvariable=self.password_var, show="*", font=("Arial", 12)).pack()
        tk.Button(root, text="Register", command=self.register, font=("Arial", 12), bg="lightblue").pack()
        tk.Button(root, text="Login", command=self.login, font=("Arial", 12), bg="lightgreen").pack()
        
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
        self.budget_window = tk.Toplevel(self.root)
        self.budget_window.title("Budget Management")
        self.budget_window.geometry("500x400")
        
        self.amount_var = tk.DoubleVar()
        self.desc_var = tk.StringVar()
        
        tk.Label(self.budget_window, text="Amount", font=("Arial", 12)).pack()
        tk.Entry(self.budget_window, textvariable=self.amount_var, font=("Arial", 12)).pack()
        tk.Label(self.budget_window, text="Description", font=("Arial", 12)).pack()
        tk.Entry(self.budget_window, textvariable=self.desc_var, font=("Arial", 12)).pack()
        tk.Button(self.budget_window, text="Add Income", command=lambda: self.add_transaction("income"), bg="lightgreen", font=("Arial", 12)).pack()
        tk.Button(self.budget_window, text="Add Expense", command=lambda: self.add_transaction("expense"), bg="lightcoral", font=("Arial", 12)).pack()
        
        self.transactions_tree = ttk.Treeview(self.budget_window, columns=("Type", "Amount", "Description"), show="headings")
        self.transactions_tree.heading("Type", text="Type")
        self.transactions_tree.heading("Amount", text="Amount")
        self.transactions_tree.heading("Description", text="Description")
        self.transactions_tree.pack(fill=tk.BOTH, expand=True)
        
        self.load_transactions()
        
    def add_transaction(self, trans_type):
        amount = self.amount_var.get()
        description = self.desc_var.get()
        conn = sqlite3.connect("budget.db")
        c = conn.cursor()
        c.execute("INSERT INTO transactions (user_id, type, amount, description) VALUES (?, ?, ?, ?)", 
                  (self.user_id, trans_type, amount, description))
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", "Transaction Added")
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
        for trans in transactions:
            self.transactions_tree.insert("", "end", values=trans)

if __name__ == "__main__":
    root = tk.Tk()
    app = BudgetApp(root)
    root.mainloop()
