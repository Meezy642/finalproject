import urllib.request
import urllib.parse
import json
import os
import sys

def safe_print(text):
    try:
        print(text)
    except UnicodeEncodeError:
        try:
            # Fallback encoding replacements for console environments like CP1252 on Windows
            encoding = sys.stdout.encoding or 'ascii'
            print(text.encode(encoding, errors='replace').decode(encoding))
        except Exception:
            pass

# Optional: Load from environment variables or a configuration dictionary
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

def load_env():
    global TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
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
                        if k == 'TELEGRAM_BOT_TOKEN' and not TELEGRAM_BOT_TOKEN:
                            TELEGRAM_BOT_TOKEN = v
                        elif k == 'TELEGRAM_CHAT_ID' and not TELEGRAM_CHAT_ID:
                            TELEGRAM_CHAT_ID = v
        except Exception:
            pass

# Load configuration variables on module import
load_env()

def send_checkout_notification(order_id, customer_name, email, phone, address, items, total_price, bot_token=None, chat_id=None, promo_code=None, discount_amount=0.0):
    """
    Constructs an HTML formatted order receipt and sends it via Telegram Bot API with inline action buttons.
    If credentials are not supplied, it logs the message locally and outputs to stdout.
    """
    token = bot_token or TELEGRAM_BOT_TOKEN
    chat = chat_id or TELEGRAM_CHAT_ID
    
    # Generate HTML text for Telegram
    msg_lines = [
        f"<b>🛒 NEW ORDER PLACED</b>",
        f"<b>Order ID:</b> #{order_id}",
        f"<b>Status:</b> Pending ⏳",
        f"<b>Customer:</b> {customer_name}",
        f"<b>Email:</b> {email}",
        f"<b>Phone:</b> {phone}",
        f"<b>Shipping Address:</b> {address}",
        f"------------------------------",
        f"<b>Items Ordered:</b>"
    ]
    
    for item in items:
        msg_lines.append(f"• {item['name']} x{item['qty']} - ${item['price']:.2f}")
        
    msg_lines.append(f"------------------------------")
    if promo_code and discount_amount > 0:
        raw_total = total_price + discount_amount
        msg_lines.append(f"<b>Subtotal:</b> ${raw_total:.2f}")
        msg_lines.append(f"<b>Promo Discount:</b> {promo_code} (-${discount_amount:.2f})")
        msg_lines.append(f"------------------------------")
    msg_lines.append(f"<b>💰 TOTAL: ${total_price:.2f}</b>")
    
    message = "\n".join(msg_lines)
    
    # Inline buttons for status updates
    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "🚚 Mark as Shipped", "callback_data": f"status_shipped:{order_id}"},
                {"text": "✅ Mark as Completed", "callback_data": f"status_completed:{order_id}"}
            ]
        ]
    }
    
    # If no credentials, simulate the notification
    if not token or not chat:
        log_message = (
            f"\n=== [SIMULATED TELEGRAM NOTIFICATION] ===\n"
            f"Config status: NOT CONFIGURED (Pass TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)\n"
            f"Message payload:\n{message}\n"
            f"Buttons: [Mark as Shipped] (status_shipped:{order_id}) | [Mark as Completed] (status_completed:{order_id})\n"
            f"=========================================\n"
        )
        safe_print(log_message)
        sys.stdout.flush()
        
        # Save simulated notification to a local log file inside the project for inspection
        log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'telegram_simulated.log')
        try:
            with open(log_file_path, 'a', encoding='utf-8') as f:
                f.write(f"--- {datetime_stamp()} ---\n{log_message}\n")
        except Exception:
            pass
            
        return {
            "status": "simulated",
            "message": message,
            "reply_markup": reply_markup,
            "error": "Telegram Bot Token or Chat ID not configured. Simulated successfully."
        }

    # Prepare actual Telegram API request
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat,
        "text": message,
        "parse_mode": "HTML",
        "reply_markup": reply_markup
    }
    
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url, 
            data=data, 
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        # Send HTTP request with 5s timeout
        with urllib.request.urlopen(req, timeout=5) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            if res_data.get('ok'):
                return {"status": "success", "message": message, "reply_markup": reply_markup, "result": res_data.get('result')}
            else:
                return {"status": "error", "message": message, "error": res_data.get('description')}
                
    except Exception as e:
        error_msg = str(e)
        safe_print(f"Error sending Telegram notification: {error_msg}")
        sys.stdout.flush()
        return {"status": "failed", "message": message, "error": error_msg}

def edit_telegram_message(token, chat_id, message_id, text, reply_markup=None):
    """
    Edits a Telegram message text and/or inline buttons.
    """
    url = f"https://api.telegram.org/bot{token}/editMessageText"
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup
    else:
        payload["reply_markup"] = {"inline_keyboard": []} # Remove keyboard
        
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url, 
            data=data, 
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        safe_print(f"Error editing Telegram message: {e}")
        return {"ok": False, "error": str(e)}

def answer_callback_query(token, callback_query_id, text):
    """
    Sends an acknowledgment response for a callback query.
    """
    url = f"https://api.telegram.org/bot{token}/answerCallbackQuery"
    payload = {
        "callback_query_id": callback_query_id,
        "text": text
    }
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url, 
            data=data, 
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        safe_print(f"Error answering callback query: {e}")
        return {"ok": False, "error": str(e)}

def datetime_stamp():
    try:
        import datetime
        return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return "unknown-time"
