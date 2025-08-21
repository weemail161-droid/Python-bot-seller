# database.py
import sqlite3

DB_FILE = "accounts.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        password TEXT,
        imap_server TEXT,
        email_login TEXT,
        email_pass TEXT,
        assigned_to TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        status TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS processed_tx (
        txid TEXT PRIMARY KEY
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        content TEXT,
        status TEXT
    )''')
    conn.commit()
    conn.close()

def add_account_row(email_, password_, imap_server_, email_login_, email_pass_):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO accounts (email, password, imap_server, email_login, email_pass) VALUES (?, ?, ?, ?, ?)",
              (email_, password_, imap_server_, email_login_, email_pass_))
    conn.commit()
    conn.close()

def assign_account(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM accounts WHERE assigned_to IS NULL LIMIT 1")
    acc = c.fetchone()
    if acc:
        c.execute("UPDATE accounts SET assigned_to=? WHERE id=?", (str(user_id), acc[0]))
        conn.commit()
    conn.close()
    return acc

def get_user_accounts(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM accounts WHERE assigned_to=?", (str(user_id),))
    accs = c.fetchall()
    conn.close()
    return accs

def add_order(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO orders (user_id, status) VALUES (?, 'pending')", (str(user_id),))
    order_id = c.lastrowid
    conn.commit()
    conn.close()
    return order_id

def get_pending_order(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM orders WHERE user_id=? AND status='pending'", (str(user_id),))
    order = c.fetchone()
    conn.close()
    return order

def update_order(order_id, status):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
    conn.commit()
    conn.close()

def is_tx_processed(txid):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT txid FROM processed_tx WHERE txid=?", (txid,))
    row = c.fetchone()
    conn.close()
    return bool(row)

def mark_tx_processed(txid):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO processed_tx (txid) VALUES (?)", (txid,))
    conn.commit()
    conn.close()

def save_message(user_id, content):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO messages (user_id, content, status) VALUES (?, ?, ?)",
              (str(user_id), content, "new"))
    conn.commit()
    conn.close()

def get_unreplied_messages():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, user_id, content FROM messages WHERE status='new' ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def mark_message_replied(msg_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE messages SET status='replied' WHERE id=?", (msg_id,))
    conn.commit()
    conn.close()

def delete_message(msg_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE messages SET status='deleted' WHERE id=?", (msg_id,))
    conn.commit()
    conn.close()