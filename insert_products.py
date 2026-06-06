import sqlite3

conn = sqlite3.connect('ecommerce.db')
cursor = conn.cursor()

# Check if products already exist
cursor.execute("SELECT COUNT(*) FROM products WHERE name='Aegis Cyber-Monitor'")
if cursor.fetchone()[0] == 0:
    cursor.execute(
        "INSERT INTO products (name, description, price, image_url, category, stock) VALUES (?, ?, ?, ?, ?, ?)",
        (
            "Aegis Cyber-Monitor",
            "Ultra-wide curved cybernetic display featuring a 240Hz refresh rate, HDR1000, and dynamic holographic backlighting for complete digital immersion.",
            399.99,
            "/static/images/cyber_monitor_v4.png",
            "Input Devices",
            12
        )
    )

cursor.execute("SELECT COUNT(*) FROM products WHERE name='Aegis Cyber-Headset'")
if cursor.fetchone()[0] == 0:
    cursor.execute(
        "INSERT INTO products (name, description, price, image_url, category, stock) VALUES (?, ?, ?, ?, ?, ?)",
        (
            "Aegis Cyber-Headset",
            "Enthusiast-grade gaming headset featuring high-fidelity spatial audio drivers, a detachable pro microphone, and passive noise-isolating memory foam earcups.",
            149.99,
            "/static/images/cyber_headset.png",
            "Audio",
            10
        )
    )

conn.commit()
conn.close()
print("Products checked and inserted successfully.")
