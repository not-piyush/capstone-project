import sqlite3
import os

DB_FILE = 'price_tracker.db'

def get_connection():
    return sqlite3.connect(DB_FILE)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS Products (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, category TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS Vendors (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, location TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS Prices (id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER, vendor_id INTEGER, price REAL NOT NULL, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(product_id) REFERENCES Products(id), FOREIGN KEY(vendor_id) REFERENCES Vendors(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS Alerts (id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER, target_price REAL NOT NULL, is_active INTEGER DEFAULT 1, FOREIGN KEY(product_id) REFERENCES Products(id))''')
    conn.commit()
    conn.close()

def add_product(name, category=""):
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute('INSERT INTO Products (name, category) VALUES (?, ?)', (name, category))
        conn.commit()
        return c.lastrowid
    except sqlite3.IntegrityError:
        c.execute('SELECT id FROM Products WHERE name = ?', (name,))
        return c.fetchone()[0]
    finally:
        conn.close()

def add_vendor(name, location=""):
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute('INSERT INTO Vendors (name, location) VALUES (?, ?)', (name, location))
        conn.commit()
        return c.lastrowid
    except sqlite3.IntegrityError:
        c.execute('SELECT id FROM Vendors WHERE name = ?', (name,))
        return c.fetchone()[0]
    finally:
        conn.close()

def add_price(product_id, vendor_id, price):
    conn = get_connection()
    c = conn.cursor()
    c.execute('INSERT INTO Prices (product_id, vendor_id, price) VALUES (?, ?, ?)', (product_id, vendor_id, price))
    conn.commit()
    conn.close()

def get_all_products():
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT id, name, category FROM Products')
    products = c.fetchall()
    conn.close()
    return products

def get_price_history(product_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT v.name, p.price, p.date
        FROM Prices p
        JOIN Vendors v ON p.vendor_id = v.id
        WHERE p.product_id = ?
        ORDER BY p.date ASC
    ''', (product_id,))
    history = c.fetchall()
    conn.close()
    return history

def add_alert(product_id, target_price):
    conn = get_connection()
    c = conn.cursor()
    c.execute('INSERT INTO Alerts (product_id, target_price) VALUES (?, ?)', (product_id, target_price))
    conn.commit()
    conn.close()

def get_active_alerts():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT a.id, p.id, p.name, a.target_price
        FROM Alerts a
        JOIN Products p ON a.product_id = p.id
        WHERE a.is_active = 1
    ''')
    alerts = c.fetchall()
    conn.close()
    return alerts
