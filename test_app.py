import unittest
import os
import json
import sqlite3
from app import app
from database import DB_PATH, init_db

class ECommerceTestCase(unittest.TestCase):
    
    def setUp(self):
        """Set up testing client and clean/init testing database."""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        
        # Reset database for tests
        if os.path.exists(DB_PATH):
            try:
                os.remove(DB_PATH)
            except PermissionError:
                pass
                
        init_db()

    def test_database_initialization(self):
        """Verify database starts with products populated."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM products")
        count = cursor.fetchone()[0]
        conn.close()
        self.assertGreater(count, 0, "Products table should be populated on database init.")

    def test_user_registration_and_login(self):
        """Verify user registration, hashing validation, and session login workflows."""
        # 1. Test registration
        response = self.client.post('/register', data={
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Connection link established', response.data)
        
        # 2. Test duplicate registration failure
        response = self.client.post('/register', data={
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Username or email address already registered', response.data)

        # 3. Test login success
        response = self.client.post('/login', data={
            'username_or_email': 'testuser',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome back, testuser', response.data)

        # Terminate session before testing login failure
        self.client.get('/logout', follow_redirects=True)

        # 4. Test login failure
        response = self.client.post('/login', data={
            'username_or_email': 'testuser',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid credentials or access key', response.data)

    def test_product_catalog(self):
        """Verify products page and product details pages load successfully."""
        # Check catalog page loads
        response = self.client.get('/products')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Hardware Catalog', response.data)
        
        # Check details of product ID 1
        response = self.client.get('/product/1')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Kinesis Mechanical Keyboard', response.data)

    def test_api_cart_resolver(self):
        """Verify JSON API endpoint resolves product metadata from cart list."""
        cart_payload = {
            "cart": [
                {"id": 1, "qty": 2},
                {"id": 2, "qty": 1}
            ]
        }
        response = self.client.post('/api/cart', 
                                    data=json.dumps(cart_payload), 
                                    content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['status'], 'success')
        self.assertEqual(len(data['items']), 2)
        self.assertEqual(data['items'][0]['id'], 1)
        self.assertEqual(data['items'][0]['qty'], 2)
        self.assertGreater(data['subtotal'], 0.0)

    def test_contact_form(self):
        """Verify message submission to the contact form persists in SQLite."""
        response = self.client.post('/contact', data={
            'name': 'Customer Support Test',
            'email': 'support@example.com',
            'message': 'This is a test message to verify database operations.'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Message package transmitted successfully', response.data)
        
        # Query db to verify record exists
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM contact_messages WHERE email='support@example.com'")
        row = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(row)
        self.assertEqual(row[1], 'Customer Support Test')

    def test_checkout_workflow(self):
        """Verify cookie-based order placement and SQLite order recording."""
        # Setup session for order
        self.client.post('/register', data={
            'username': 'buyer',
            'email': 'buyer@example.com',
            'password': 'password123'
        })
        self.client.post('/login', data={
            'username_or_email': 'buyer',
            'password': 'password123'
        })

        # Set cart cookie (simulates JS cookie-write)
        # Note: cart.js saves: [{"id": 1, "qty": 2}]
        cart_cookie_data = '[{"id": 1, "qty": 2}]'
        self.client.set_cookie('shopping_cart', cart_cookie_data)

        # Post checkout form
        response = self.client.post('/checkout', data={
            'customer_name': 'Buyer Name',
            'email': 'buyer@example.com',
            'phone': '1234567890',
            'address': 'Grid Coordinate 55, Sector 4'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Order dispatched successfully', response.data)
        
        # Verify database has order record
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE email='buyer@example.com'")
        order = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(order, "Order record should be saved in database.")
        self.assertEqual(order[2], 'Buyer Name')
        self.assertEqual(order[5], 'Grid Coordinate 55, Sector 4')
        self.assertIn('Kinesis Mechanical Keyboard', order[6])


        # 4. Test Update Status Route
        response = self.client.get(f'/admin/update-status/{order[0]}/Completed', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'status updated to Completed', response.data)

        # Verify database status changed
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM orders WHERE id=?", (order[0],))
        status = cursor.fetchone()[0]
        conn.close()
        self.assertEqual(status, 'Completed', "Order status should be updated to Completed in the DB.")
        
if __name__ == '__main__':
    unittest.main()
