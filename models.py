import hashlib
import secrets
import datetime
import sqlite3
from database import get_db_connection

# Secure hashing configurations
SALT_LENGTH = 16
HASH_ITERATIONS = 100000
HASH_ALGORITHM = 'sha256'

def hash_password(password):
    """Generate a secure salt and PBKDF2 password hash."""
    salt = secrets.token_hex(SALT_LENGTH)
    pwd_hash = hashlib.pbkdf2_hmac(
        HASH_ALGORITHM,
        password.encode('utf-8'),
        salt.encode('utf-8'),
        HASH_ITERATIONS
    ).hex()
    return f"{salt}${pwd_hash}"

def verify_password(stored_hash, password):
    """Verify a password against its stored PBKDF2 hash."""
    try:
        salt, pwd_hash = stored_hash.split('$')
        new_hash = hashlib.pbkdf2_hmac(
            HASH_ALGORITHM,
            password.encode('utf-8'),
            salt.encode('utf-8'),
            HASH_ITERATIONS
        ).hex()
        return secrets.compare_digest(pwd_hash, new_hash)
    except ValueError:
        return False

# USER MODULES

def create_user(username, email, password):
    """Register a new user after hashing their password."""
    password_hash = hash_password(password)
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, password_hash)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def authenticate_user(username_or_email, password):
    """Authenticate a user by matching their username/email and verifying the password."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE username = ? OR email = ?",
        (username_or_email, username_or_email)
    )
    user = cursor.fetchone()
    conn.close()
    
    if user and verify_password(user['password_hash'], password):
        return {
            'id': user['id'],
            'username': user['username'],
            'email': user['email']
        }
    return None

def get_user_by_email(email):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def update_user_profile(user_id, username, email):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE users SET username = ?, email = ? WHERE id = ?",
            (username, email, user_id)
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()

def update_password(user_id, new_password):
    password_hash = hash_password(new_password)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (password_hash, user_id)
    )
    conn.commit()
    conn.close()
    return True

# PASSWORD RESET MODULE

def create_reset_token(email):
    """Generate and store a secure 6-digit verification code for a user, valid for 15 minutes."""
    import random
    user = get_user_by_email(email)
    if not user:
        return None
    
    # Generate 6-digit verification code
    code = f"{random.randint(100000, 999999)}"
    expiry = (datetime.datetime.now() + datetime.timedelta(minutes=15)).strftime('%Y-%m-%d %H:%M:%S')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET reset_token = ?, reset_token_expiry = ? WHERE email = ?",
        (code, expiry, email)
    )
    conn.commit()
    conn.close()
    return code

def verify_reset_code(email, code):
    """Verify reset code validity for a specific email. Return user object if valid, else None."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(
        "SELECT * FROM users WHERE email = ? AND reset_token = ? AND reset_token_expiry > ?",
        (email, code, now_str)
    )
    user = cursor.fetchone()
    conn.close()
    return user

def verify_reset_token(token):
    """Verify reset token validity (fallback for compatibility). Return user object if valid, else None."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(
        "SELECT * FROM users WHERE reset_token = ? AND reset_token_expiry > ?",
        (token, now_str)
    )
    user = cursor.fetchone()
    conn.close()
    return user

def clear_reset_token(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET reset_token = NULL, reset_token_expiry = NULL WHERE id = ?",
        (user_id,)
    )
    conn.commit()
    conn.close()

# CONTACT MODULE

def save_contact_message(name, email, message):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO contact_messages (name, email, message) VALUES (?, ?, ?)",
        (name, email, message)
    )
    conn.commit()
    conn.close()
    return True

# PRODUCTS MODULE

def get_all_products(category=None, search_query=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM products WHERE 1=1"
    params = []
    
    if category:
        query += " AND category = ?"
        params.append(category)
        
    if search_query:
        query += " AND (name LIKE ? OR description LIKE ?)"
        params.extend([f"%{search_query}%", f"%{search_query}%"])
        
    cursor.execute(query, params)
    products = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return products

def get_product_by_id(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    conn.close()
    return dict(product) if product else None

def get_product_categories():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT category FROM products")
    categories = [row[0] for row in cursor.fetchall()]
    conn.close()
    return categories

# ORDERS MODULE

def create_order(user_id, customer_name, email, phone, address, items_json, total_price):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO orders (user_id, customer_name, email, phone, address, items_json, total_price) 
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (user_id, customer_name, email, phone, address, items_json, total_price)
    )
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return order_id

def get_user_orders(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    )
    orders = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return orders

def get_all_orders():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders ORDER BY created_at DESC")
    orders = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return orders

def update_order_status(order_id, status):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE orders SET status = ? WHERE id = ?",
        (status, order_id)
    )
    conn.commit()
    conn.close()
    return True

def get_order_by_id(order_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    order = cursor.fetchone()
    conn.close()
    return dict(order) if order else None
