import sqlite3
import os

DB_FILE = 'price_tracker.db'

def get_connection():
    return sqlite3.connect(DB_FILE)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS Users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, discord_webhook TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS Products (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, category TEXT, user_id INTEGER, tracking_url TEXT, FOREIGN KEY(user_id) REFERENCES Users(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS Vendors (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, location TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS Prices (id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER, vendor_id INTEGER, price REAL NOT NULL, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(product_id) REFERENCES Products(id), FOREIGN KEY(vendor_id) REFERENCES Vendors(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS Alerts (id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER, target_price REAL NOT NULL, is_active INTEGER DEFAULT 1, user_id INTEGER, FOREIGN KEY(product_id) REFERENCES Products(id), FOREIGN KEY(user_id) REFERENCES Users(id))''')
    conn.commit()
    conn.close()

def add_user(username, password_hash):
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute('INSERT INTO Users (username, password_hash) VALUES (?, ?)', (username, password_hash))
        conn.commit()
        return c.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def get_user_by_username(username):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT id, username, password_hash FROM Users WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT id, username, password_hash, discord_webhook FROM Users WHERE id = ?', (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def update_webhook(user_id, webhook_url):
    conn = get_connection()
    c = conn.cursor()
    c.execute('UPDATE Users SET discord_webhook = ? WHERE id = ?', (webhook_url, user_id))
    conn.commit()
    conn.close()

def add_product(name, category="", user_id=None, tracking_url=None):
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute('INSERT INTO Products (name, category, user_id, tracking_url) VALUES (?, ?, ?, ?)', (name, category, user_id, tracking_url))
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

def get_all_products(user_id=None):
    conn = get_connection()
    c = conn.cursor()
    if user_id:
        c.execute('SELECT id, name, category, tracking_url FROM Products WHERE user_id = ? OR user_id IS NULL', (user_id,))
    else:
        c.execute('SELECT id, name, category, tracking_url FROM Products')
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

def add_alert(product_id, target_price, user_id=None):
    conn = get_connection()
    c = conn.cursor()
    c.execute('INSERT INTO Alerts (product_id, target_price, user_id) VALUES (?, ?, ?)', (product_id, target_price, user_id))
    conn.commit()
    conn.close()

def get_active_alerts(user_id=None):
    conn = get_connection()
    c = conn.cursor()
    if user_id:
        c.execute('''
            SELECT a.id, p.id, p.name, a.target_price, a.user_id, p.tracking_url
            FROM Alerts a
            JOIN Products p ON a.product_id = p.id
            WHERE a.is_active = 1 AND a.user_id = ?
        ''', (user_id,))
    else:
        c.execute('''
            SELECT a.id, p.id, p.name, a.target_price, a.user_id, p.tracking_url
            FROM Alerts a
            JOIN Products p ON a.product_id = p.id
            WHERE a.is_active = 1
        ''')
    alerts = c.fetchall()
    conn.close()
    return alerts

def deactivate_alert(alert_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('UPDATE Alerts SET is_active = 0 WHERE id = ?', (alert_id,))
    conn.commit()
    conn.close()
