import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ecommerce.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
        if cursor.fetchone():
            cursor.execute("DELETE FROM products WHERE name IN ('Aegis Cyber-Helmet', 'Aegis Cyber-Monitor', 'Aegis Cyber-Headset', 'Chronos Quantum Watch', 'Nexus Charging Dock', 'Lumen Smart Desk Mat')")
            conn.commit()
            
            mock_products = [
                ("Kinesis Mechanical Keyboard", "65% enthusiast mechanical keyboard with hot-swappable linear jade switches, sound-damped frosted glass body, and customized addressable RGB matrix lighting.", 189.50, "/static/images/keyboard.png", "Input Devices", 8),
                ("Orion Nebula Earbuds", "Wireless audiophile earbuds delivering high-fidelity spatial audio, 40dB hybrid active noise cancellation, and a sleek titanium charging case with wireless power transfer.", 249.00, "/static/images/earbuds.png", "Audio", 15),
                ("ASUS Cyber-Monitor", "Ultra-wide curved cybernetic display featuring a 240Hz refresh rate, HDR1000, and dynamic holographic backlighting for complete digital immersion.", 399.99, "/static/images/cyber_monitor_v4.png", "Input Devices", 12),
                ("Logitech Cyber-Headset", "Enthusiast-grade gaming headset featuring high-fidelity spatial audio drivers, a detachable pro microphone, and passive noise-isolating memory foam earcups.", 149.99, "/static/images/cyber_headset.png", "Audio", 10),
                ("Razer Cyber-Mouse", "Enthusiast-grade wireless gaming mouse featuring an ultra-lightweight design, high-precision optical sensor, and low-latency wireless connection.", 99.99, "/static/images/cyber_mouse.png", "Input Devices", 15),
                ("mnus chkout", "Exclusive zero-cost promotional checkout testing item.", 0.00, "/static/images/cyber_monitor_v4.png", "Promotions", 100)
            ]
            for name, desc, price, img, cat, stock in mock_products:
                cursor.execute("SELECT COUNT(*) FROM products WHERE name = ?", (name,))
                if cursor.fetchone()[0] == 0:
                    cursor.execute(
                        "INSERT INTO products (name, description, price, image_url, category, stock) VALUES (?, ?, ?, ?, ?, ?)",
                        (name, desc, price, img, cat, stock)
                    )
                else:
                    cursor.execute(
                        "UPDATE products SET description=?, price=?, image_url=?, category=?, stock=? WHERE name=?",
                        (desc, price, img, cat, stock, name)
                    )
            conn.commit()
    except Exception:
        pass
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        reset_token TEXT,
        reset_token_expiry TIMESTAMP
    )
    ''')
    
    # Create Products table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        price REAL NOT NULL,
        image_url TEXT NOT NULL,
        category TEXT NOT NULL,
        stock INTEGER NOT NULL DEFAULT 10
    )
    ''')
    
    # Create Contact Messages table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS contact_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        message TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create Orders table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        customer_name TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT NOT NULL,
        address TEXT NOT NULL,
        items_json TEXT NOT NULL,
        total_price REAL NOT NULL,
        status TEXT DEFAULT 'Pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Purge deprecated products if they exist
    cursor.execute("DELETE FROM products WHERE name IN ('Aegis Cyber-Helmet', 'Aegis Cyber-Monitor', 'Aegis Cyber-Headset', 'Chronos Quantum Watch', 'Nexus Charging Dock', 'Lumen Smart Desk Mat')")
    conn.commit()
    
    mock_products = [
        (
            "Kinesis Mechanical Keyboard",
            "65% enthusiast mechanical keyboard with hot-swappable linear jade switches, sound-damped frosted glass body, and customized addressable RGB matrix lighting.",
            189.50,
            "/static/images/keyboard.png",
            "Input Devices",
            8
        ),
        (
            "Orion Nebula Earbuds",
            "Wireless audiophile earbuds delivering high-fidelity spatial audio, 40dB hybrid active noise cancellation, and a sleek titanium charging case with wireless power transfer.",
            249.00,
            "/static/images/earbuds.png",
            "Audio",
            15
        ),
        (
            "ASUS Cyber-Monitor",
            "Ultra-wide curved cybernetic display featuring a 240Hz refresh rate, HDR1000, and dynamic holographic backlighting for complete digital immersion.",
            399.99,
            "/static/images/cyber_monitor_v4.png",
            "Input Devices",
            12
        ),
        (
            "Logitech Cyber-Headset",
            "Enthusiast-grade gaming headset featuring high-fidelity spatial audio drivers, a detachable pro microphone, and passive noise-isolating memory foam earcups.",
            149.99,
            "/static/images/cyber_headset.png",
            "Audio",
            10
        ),
        (
            "Razer Cyber-Mouse",
            "Enthusiast-grade wireless gaming mouse featuring an ultra-lightweight design, high-precision optical sensor, and low-latency wireless connection.",
            99.99,
            "/static/images/cyber_mouse.png",
            "Input Devices",
            15
        ),
        (
            "mnus chkout",
            "Exclusive zero-cost promotional checkout testing item.",
            0.00,
            "/static/images/cyber_monitor_v4.png",
            "Promotions",
            100
        )
    ]
    for name, desc, price, img, cat, stock in mock_products:
        cursor.execute("SELECT COUNT(*) FROM products WHERE name = ?", (name,))
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO products (name, description, price, image_url, category, stock) VALUES (?, ?, ?, ?, ?, ?)",
                (name, desc, price, img, cat, stock)
            )
        else:
            cursor.execute(
                "UPDATE products SET description=?, price=?, image_url=?, category=?, stock=? WHERE name=?",
                (desc, price, img, cat, stock, name)
            )
    conn.commit()
        
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully.")
