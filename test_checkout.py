import urllib.request
import urllib.parse
import http.cookiejar

# Create a cookie processor to handle the cart cookie
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# Setup shopping_cart cookie: [{"id": 1, "qty": 2}] (URL-encoded)
cart_cookie = http.cookiejar.Cookie(
    version=0, name='shopping_cart', value='%5B%7B%22id%22%3A1%2C%22qty%22%3A2%7D%5D',
    port=None, port_specified=False,
    domain='127.0.0.1', domain_specified=False, domain_initial_dot=False,
    path='/', path_specified=True,
    secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={}, rfc2109=False
)
cj.set_cookie(cart_cookie)

# Prepare checkout form payload
payload = {
    'customer_name': 'Aetheria Client',
    'email': 'client@aetheria.io',
    'phone': '+1 555-0987',
    'address': 'Neo-Tokyo Sector 4'
}

data = urllib.parse.urlencode(payload).encode('utf-8')
req = urllib.request.Request("http://127.0.0.1:5000/checkout", data=data, method='POST')

print("Sending checkout payload...")
try:
    with opener.open(req) as res:
        print("Order placed! Status code:", res.status)
        print("Redirected to URL:", res.url)
except Exception as e:
    print("Error during checkout simulation:", e)
