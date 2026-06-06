import os
import json
import secrets
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from database import init_db
import models
import telegram_notifier

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Ensure database is initialized on startup
with app.app_context():
    init_db()

# Custom template filter to load JSON strings easily if needed
@app.template_filter('from_json')
def from_json_filter(val):
    try:
        return json.loads(val)
    except Exception:
        return []

# Helper: Require authentication
def require_login():
    if 'user' not in session:
        flash("Authorization required. Please log in.", "error")
        return False
    return True

# 1. HOME MODULE
@app.route('/')
def home():
    # Fetch categories and first 4 products for homepage showcase
    categories = models.get_product_categories()
    products = models.get_all_products()[:4]
    
    # Check if there is simulated telegram modal data in session to render
    telegram_modal_data = session.pop('telegram_simulated_modal', None)
    
    return render_template(
        'home.html', 
        products=products, 
        categories=categories,
        telegram_modal_data=telegram_modal_data
    )

# 2. PRODUCTS CATALOG MODULE
@app.route('/products')
def products():
    category = request.args.get('category')
    search_query = request.args.get('search')
    
    categories = models.get_product_categories()
    products_list = models.get_all_products(category=category, search_query=search_query)
    
    return render_template(
        'products.html',
        products=products_list,
        categories=categories,
        selected_category=category,
        search_query=search_query
    )

# 3. PRODUCT DETAILS MODULE
@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = models.get_product_by_id(product_id)
    if not product:
        flash("Requested product does not exist in catalog.", "error")
        return redirect(url_for('products'))
    return render_template('product_detail.html', product=product)

# 4. CONTACT MODULE
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        
        if not name or not email or not message:
            flash("All contact parameters are required.", "error")
        else:
            models.save_contact_message(name, email, message)
            flash("Message package transmitted successfully. Our guild will follow up.", "success")
            return redirect(url_for('contact'))
            
    return render_template('contact.html')

# 5. AUTHENTICATION MODULES (REGISTER, LOGIN, LOGOUT, PROFILE UPDATE)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user' in session:
        return redirect(url_for('account'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not username or not email or not password:
            flash("All registration fields are required.", "error")
        elif len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
        else:
            success = models.create_user(username, email, password)
            if success:
                flash("Connection link established. Please login to authenticate.", "success")
                return redirect(url_for('login'))
            else:
                flash("Username or email address already registered.", "error")
                
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('account'))
        
    if request.method == 'POST':
        username_or_email = request.form.get('username_or_email')
        password = request.form.get('password')
        
        user = models.authenticate_user(username_or_email, password)
        if user:
            session['user'] = user
            flash(f"Welcome back, {user['username']}. Session established.", "success")
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/') and not next_page.startswith('//'):
                return redirect(next_page)
            return redirect(url_for('home'))
        else:
            flash("Invalid credentials or access key.", "error")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("Session terminated. Connection closed.", "success")
    return redirect(url_for('home'))

@app.route('/account')
def account():
    if not require_login():
        return redirect(url_for('login'))
        
    active_tab = request.args.get('tab', 'profile')
    if active_tab not in ['profile', 'orders']:
        active_tab = 'profile'
        
    user_id = session['user']['id']
    user_data = models.get_user_by_id(user_id)
    orders = models.get_user_orders(user_id)
    
    # Parse order items JSON for template loops
    for order in orders:
        try:
            order['items_list'] = json.loads(order['items_json'])
        except Exception:
            order['items_list'] = []
            
    return render_template('account.html', user=user_data, orders=orders, active_tab=active_tab)

@app.route('/history')
def order_history():
    if not require_login():
        return redirect(url_for('login'))
    return redirect(url_for('account', tab='orders'))

@app.route('/account/update-profile', methods=['POST'])
def account_update_profile():
    if not require_login():
        return redirect(url_for('login'))
        
    username = request.form.get('username')
    email = request.form.get('email')
    user_id = session['user']['id']
    
    if not username or not email:
        flash("Username and Email fields cannot be blank.", "error")
    else:
        success = models.update_user_profile(user_id, username, email)
        if success:
            session['user']['username'] = username
            session['user']['email'] = email
            flash("Node profile details updated successfully.", "success")
        else:
            flash("Could not update profile. Username or email might be taken.", "error")
            
    return redirect(url_for('account'))

@app.route('/account/update-password', methods=['POST'])
def account_update_password():
    if not require_login():
        return redirect(url_for('login'))
        
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    user_id = session['user']['id']
    
    # Verify current password
    user_data = models.get_user_by_id(user_id)
    if not models.verify_password(user_data['password_hash'], old_password):
        flash("Current password verification failed.", "error")
    elif len(new_password) < 6:
        flash("New password must be at least 6 characters.", "error")
    else:
        models.update_password(user_id, new_password)
        flash("Security credentials updated. Protect your node.", "success")
        
    return redirect(url_for('account'))

# 6. PASSWORD RESET MODULE

# SMTP Configuration defaults
SMTP_CONFIG = {
    'SMTP_SERVER': 'smtp.gmail.com',
    'SMTP_PORT': 587,
    'SMTP_USERNAME': '',
    'SMTP_PASSWORD': '',
    'SMTP_SENDER': ''
}

def load_smtp_env():
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        k, v = line.split('=', 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k in SMTP_CONFIG:
                            if k == 'SMTP_PORT':
                                SMTP_CONFIG[k] = int(v)
                            else:
                                SMTP_CONFIG[k] = v
        except Exception:
            pass

def send_reset_email(to_email, reset_code):
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    # Make sure env is updated
    load_smtp_env()

    server_addr = SMTP_CONFIG.get('SMTP_SERVER') or 'smtp.gmail.com'
    port = SMTP_CONFIG.get('SMTP_PORT') or 587
    username = SMTP_CONFIG.get('SMTP_USERNAME')
    password = SMTP_CONFIG.get('SMTP_PASSWORD')
    sender = SMTP_CONFIG.get('SMTP_SENDER') or username
    
    if not username or not password:
        return False, "SMTP credentials not configured. Please define SMTP_USERNAME and SMTP_PASSWORD in your .env file."
        
    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = to_email
    msg['Subject'] = "YSTAA Shop - Password Reset Code"
    
    body = f"""Hello,

You requested a password reset for your account at YSTAA Shop.
Your secure 6-digit verification code is:

👉   {reset_code}   👈

Enter this code on the verification page to set your new password. This code is valid for 15 minutes.

If you did not make this request, please ignore this email.

Best regards,
YSTAA Shop Team
"""
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP(server_addr, port, timeout=10)
        server.starttls()
        server.login(username, password)
        server.sendmail(sender, to_email, msg.as_string())
        server.quit()
        return True, "Success"
    except Exception as e:
        return False, str(e)

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form.get('email')
        code = models.create_reset_token(email) # Generates the 6-digit code
        
        if code:
            # Try to send real email
            sent_ok, details = send_reset_email(email, code)
            
            # Print simulation logs to outbox file / console as well for backup
            log_msg = (
                f"\n=== [SIMULATED RESET EMAIL OUTBOX] ===\n"
                f"To: {email}\n"
                f"Subject: Password Restoration Code\n"
                f"Body: Your 6-digit recovery code is: {code}\n"
                f"=======================================\n"
            )
            print(log_msg)
            
            log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reset_emails.log')
            try:
                with open(log_file_path, 'a', encoding='utf-8') as f:
                    f.write(log_msg)
            except Exception:
                pass
                
            if sent_ok:
                flash(f"Recovery code sent successfully to {email}.", "success")
            else:
                flash(f"Real email delivery failed ({details}). Code outputted to server logs: {code}", "warning")
                
            return redirect(url_for('reset_password_verify', email=email))
        else:
            # We don't reveal user existence, but for the local project, we guide the user
            flash("If that email is registered, a restoration code is available in server logs.", "success")
            return redirect(url_for('login'))
        
    return render_template('reset_password.html')

@app.route('/reset-password-verify', methods=['GET', 'POST'])
def reset_password_verify():
    email = request.args.get('email', '')
    
    if request.method == 'POST':
        email = request.form.get('email')
        code = request.form.get('code')
        new_password = request.form.get('new_password')
        
        if not email or not code or not new_password:
            flash("All fields are required.", "error")
            return render_template('reset_password_verify.html', email=email)
            
        user = models.verify_reset_code(email, code)
        if not user:
            flash("Invalid or expired password recovery code.", "error")
            return render_template('reset_password_verify.html', email=email)
            
        if len(new_password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template('reset_password_verify.html', email=email)
            
        models.update_password(user['id'], new_password)
        models.clear_reset_token(user['id'])
        flash("Credentials restored successfully. Please login with your new password.", "success")
        return redirect(url_for('login'))
        
    return render_template('reset_password_verify.html', email=email)

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password_token(token):
    # Backward compatibility fallback
    user = models.verify_reset_token(token)
    if not user:
        flash("Invalid or expired password recovery token.", "error")
        return redirect(url_for('reset_password'))
        
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        if not new_password or len(new_password) < 6:
            flash("Password must be at least 6 characters.", "error")
        else:
            models.update_password(user['id'], new_password)
            models.clear_reset_token(user['id'])
            flash("Credentials restored successfully. Please login with new password.", "success")
            return redirect(url_for('login'))
            
    return render_template('reset_password.html', token=token, user=user)

# 7. CART COOKIE RESOLVER API
@app.route('/api/cart', methods=['POST'])
def api_cart():
    req_data = request.get_json() or {}
    cart_items = req_data.get('cart', [])
    
    detailed_items = []
    subtotal = 0.0
    
    for cart_item in cart_items:
        try:
            prod_id = int(cart_item.get('id'))
            qty = int(cart_item.get('qty', 1))
            
            product = models.get_product_by_id(prod_id)
            if product:
                item_total = product['price'] * qty
                subtotal += item_total
                detailed_items.append({
                    'id': product['id'],
                    'name': product['name'],
                    'price': product['price'],
                    'image_url': product['image_url'],
                    'category': product['category'],
                    'qty': qty
                })
        except (ValueError, TypeError):
            continue
            
    return jsonify({
        'status': 'success',
        'items': detailed_items,
        'subtotal': subtotal,
        'total': subtotal # Zero delivery cost
    })

# 8. CHECKOUT MODULE
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'user' not in session:
        flash("Please sign in or sign up to complete your purchase.", "info")
        return redirect(url_for('login', next=request.path))
        
    if request.method == 'POST':
        customer_name = request.form.get('customer_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address')
        
        # Retrieve and calculate promo discount
        applied_promo = request.form.get('applied_promo', '').strip().upper()
        discount_pct = 0.0
        if applied_promo:
            if applied_promo in ['YSTAA10', 'SAVE10']:
                discount_pct = 0.10
            elif applied_promo in ['YSTAA20', 'SAVE20']:
                discount_pct = 0.20
            elif applied_promo in ['YSTAA50']:
                discount_pct = 0.50
        
        # Parse Cart Cookie directly
        cart_cookie = request.cookies.get('shopping_cart', '[]')
        try:
            cart_raw = json.loads(urllib_unquote(cart_cookie))
        except Exception:
            cart_raw = []
            
        if not cart_raw:
            flash("Your cart is empty. Cannot dispatch order.", "error")
            return redirect(url_for('products'))
            
        if not customer_name or not email or not phone or not address:
            flash("All shipping coordinates are required.", "error")
            return redirect(url_for('checkout'))
            
        # Compile items details and check prices/availability
        items_detail = []
        total_price = 0.0
        
        for item in cart_raw:
            prod = models.get_product_by_id(int(item['id']))
            if prod:
                qty = int(item['qty'])
                items_detail.append({
                    'id': prod['id'],
                    'name': prod['name'],
                    'price': prod['price'],
                    'qty': qty,
                    'category': prod['category']
                })
                total_price += prod['price'] * qty
                
        if not items_detail:
            flash("Invalid items in cart.", "error")
            return redirect(url_for('products'))
            
        # Create database record
        user_id = session['user']['id'] if 'user' in session else None
        
        discount_amount = total_price * discount_pct
        final_price = total_price - discount_amount
        
        order_id = models.create_order(
            user_id, 
            customer_name, 
            email, 
            phone, 
            address, 
            json.dumps(items_detail), 
            final_price
        )
        
        # Send Telegram notification
        notify_res = telegram_notifier.send_checkout_notification(
            order_id=order_id,
            customer_name=customer_name,
            email=email,
            phone=phone,
            address=address,
            items=items_detail,
            total_price=final_price,
            promo_code=applied_promo if discount_pct > 0 else None,
            discount_amount=discount_amount
        )
        
        # Clear Cart Cookie via response and redirect
        resp = redirect(url_for('home'))
        resp.set_cookie('shopping_cart', '', expires=0, path='/')
        
        flash("Order dispatched successfully. Check Telegram logs.", "success")
        
        # If notification was simulated, store in session to render the modal visualizer on home
        if notify_res.get('status') == 'simulated':
            session['telegram_simulated_modal'] = {
                'message': notify_res.get('message'),
                'order_id': order_id
            }
            
        return resp
        
    return render_template('checkout.html')

# 9. SELLER ADMIN PORTAL MODULES
@app.route('/admin/update-status/<int:order_id>/<string:new_status>')
def admin_update_status(order_id, new_status):
    if new_status not in ['Pending', 'Shipped', 'Completed']:
        flash("Invalid order status code.", "error")
        return redirect(url_for('home'))
        
    models.update_order_status(order_id, new_status)
    flash(f"Order #{order_id} status updated to {new_status}!", "success")
    return redirect(url_for('home'))

# Helper: urllib unquote for cookie parsing
def urllib_unquote(s):
    try:
        import urllib.parse
        return urllib.parse.unquote(s)
    except Exception:
        return s

# Background Telegram Polling Thread Logic
import threading
import time
import urllib.request

def handle_telegram_callback(token, callback):
    callback_id = callback.get('id')
    chat_id = callback.get('message', {}).get('chat', {}).get('id')
    message_id = callback.get('message', {}).get('message_id')
    data = callback.get('data', '')
    
    if not data or not chat_id or not message_id:
        return
        
    if ':' not in data:
        return
        
    action, order_id_str = data.split(':', 1)
    try:
        order_id = int(order_id_str)
    except ValueError:
        return
        
    new_status = None
    if action == 'status_shipped':
        new_status = 'Shipped'
    elif action == 'status_completed':
        new_status = 'Completed'
        
    if not new_status:
        return
        
    # Update status in SQLite
    models.update_order_status(order_id, new_status)
    
    # Retrieve updated details to reconstruct the message text
    order = models.get_order_by_id(order_id)
    if not order:
        return
        
    status_text = f"Shipped 🚚" if new_status == 'Shipped' else f"Completed ✅"
    
    msg_lines = [
        f"<b>🛒 NEW ORDER PLACED</b>",
        f"<b>Order ID:</b> #{order['id']}",
        f"<b>Status:</b> {status_text}",
        f"<b>Customer:</b> {order['customer_name']}",
        f"<b>Email:</b> {order['email']}",
        f"<b>Phone:</b> {order['phone']}",
        f"<b>Shipping Address:</b> {order['address']}",
        f"------------------------------",
        f"<b>Items Ordered:</b>"
    ]
    
    try:
        items = json.loads(order['items_json'])
    except Exception:
        items = []
        
    for item in items:
        msg_lines.append(f"• {item['name']} x{item['qty']} - ${item['price']:.2f}")
        
    msg_lines.append(f"------------------------------")
    msg_lines.append(f"<b>💰 TOTAL: ${order['total_price']:.2f}</b>")
    
    new_message_text = "\n".join(msg_lines)
    
    # Edit inline keyboard options
    reply_markup = None
    if new_status == 'Shipped':
        reply_markup = {
            "inline_keyboard": [
                [
                    {"text": "✅ Mark as Completed", "callback_data": f"status_completed:{order_id}"}
                ]
            ]
        }
    else:
        # Completed status has no action keyboard
        reply_markup = {"inline_keyboard": []}
        
    telegram_notifier.edit_telegram_message(token, chat_id, message_id, new_message_text, reply_markup)
    telegram_notifier.answer_callback_query(token, callback_id, f"Order #{order_id} marked as {new_status}")

def run_telegram_poller():
    token = telegram_notifier.TELEGRAM_BOT_TOKEN
    if not token:
        print("Telegram Bot Token not configured. Polling thread disabled.")
        return
        
    print(f"Telegram Bot Polling loop started for token prefix: {token.split(':')[0]}")
    offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{token}/getUpdates?offset={offset}&timeout=10"
            req = urllib.request.Request(url, method='GET')
            with urllib.request.urlopen(req, timeout=15) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                if res_data.get('ok'):
                    updates = res_data.get('result', [])
                    for update in updates:
                        offset = update.get('update_id') + 1
                        if 'callback_query' in update:
                            handle_telegram_callback(token, update['callback_query'])
        except Exception as e:
            # Delay before retry to prevent API spamming
            time.sleep(5)

if __name__ == '__main__':
    # Start background Telegram updater if we are in the main Werkzeug worker or debug is off
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
        polling_thread = threading.Thread(target=run_telegram_poller, daemon=True)
        polling_thread.start()
        
    # Running on local port 5000
    app.run(debug=True, host='127.0.0.1', port=5000)
