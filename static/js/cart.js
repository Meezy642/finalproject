// Cookie Cart Management Module

// Helper: Get Cookie
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) {
        try {
            return JSON.parse(decodeURIComponent(parts.pop().split(';').shift()));
        } catch (e) {
            console.error("Error parsing cart cookie, resetting.", e);
            return [];
        }
    }
    return [];
}

// Helper: Set Cookie
function setCookie(name, value, days = 30) {
    const date = new Date();
    date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
    const expires = `; expires=${date.toUTCString()}`;
    document.cookie = `${name}=${encodeURIComponent(JSON.stringify(value))}${expires}; path=/; SameSite=Lax`;
}

// Get Cart Items
function getCart() {
    return getCookie('shopping_cart') || [];
}

// Save Cart Items
function saveCart(cart) {
    setCookie('shopping_cart', cart);
    updateCartUI();
}

// Add Item to Cart
function addToCart(productId, qty = 1) {
    productId = parseInt(productId);
    let cart = getCart();
    let existingItem = cart.find(item => item.id === productId);
    
    if (existingItem) {
        existingItem.qty += qty;
    } else {
        cart.push({ id: productId, qty: qty });
    }
    
    saveCart(cart);
    showToast("Item added to cart", "success");
    openCartDrawer();
}

// Modify Quantity (+ or -)
function modifyQty(productId, delta) {
    productId = parseInt(productId);
    let cart = getCart();
    let item = cart.find(item => item.id === productId);
    
    if (item) {
        item.qty += delta;
        if (item.qty <= 0) {
            cart = cart.filter(i => i.id !== productId);
            showToast("Item removed from cart", "success");
        } else {
            showToast("Cart updated", "success");
        }
        saveCart(cart);
    }
}

// Remove Item from Cart
function removeFromCart(productId) {
    productId = parseInt(productId);
    let cart = getCart();
    cart = cart.filter(item => item.id !== productId);
    saveCart(cart);
    showToast("Item removed from cart", "success");
}

// Clear Cart
function clearCart() {
    setCookie('shopping_cart', [], -1); // delete cookie
    updateCartUI();
}

// Update Cart Badge and Drawer Content
function updateCartUI() {
    const cart = getCart();
    const totalCount = cart.reduce((sum, item) => sum + item.qty, 0);
    
    // Update Badge (Navbar)
    const badges = document.querySelectorAll('.cart-badge');
    badges.forEach(badge => {
        badge.textContent = totalCount;
        if (totalCount > 0) {
            badge.style.display = 'flex';
        } else {
            badge.style.display = 'none';
        }
    });

    // Populate Cart Drawer if open
    const drawerContainer = document.getElementById('cart-items-list');
    if (!drawerContainer) return;
    
    if (cart.length === 0) {
        drawerContainer.innerHTML = `
            <div class="cart-empty-message">
                <svg fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 10.5V6a3.75 3.75 0 1,0-7.5 0v4.5m11.356-1.993 1.263 12c.07.665-.45 1.243-1.119 1.243H4.25a1.125 1.125 0 0,1-1.12-1.243l1.264-12A1.125 1.125 0 0,1 5.513 7.5h12.974c.576 0 1.059.435 1.119 1.007ZM8.625 10.5a.375 0 1,1-.75 0 .375 0 0,1 .75 0Zm7.5 0a.375 0 1,1-.75 0 .375 0 0,1 .75 0Z" />
                </svg>
                <p>Your cart is empty</p>
            </div>
        `;
        document.getElementById('cart-drawer-subtotal').textContent = '$0.00';
        document.getElementById('cart-drawer-total').textContent = '$0.00';
        
        const checkoutBtn = document.getElementById('cart-checkout-btn');
        if (checkoutBtn) checkoutBtn.disabled = true;
        return;
    }

    // Fetch details of items in the cart
    fetch('/api/cart', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ cart: cart })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            let itemsHtml = '';
            data.items.forEach(item => {
                itemsHtml += `
                    <div class="cart-item">
                        <div class="cart-item-img">
                            <img src="${item.image_url}" alt="${item.name}" onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
                            <svg style="display:none;" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" fill="none">
                                <path stroke-linecap="round" stroke-linejoin="round" d="m2.25 15.75 5.159-5.159a2.25 2.25 0 0 1 3.182 0l5.159 5.159m-1.5-1.5 1.409-1.409a2.25 2.25 0 0 1 3.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 0 0 1.5-1.5V6a1.5 1.5 0 0 0-1.5-1.5H3.75A1.5 1.5 0 0 0 2.25 6v12a1.5 1.5 0 0 0 1.5 1.5Zm10.5-11.25h.008v.008h-.008V8.25Zm.375 0a.375 0 1 1-.75 0 .375 0 0 1 .75 0Z" />
                            </svg>
                        </div>
                        <div class="cart-item-details">
                            <h4 class="cart-item-name"><a href="/product/${item.id}">${item.name}</a></h4>
                            <div class="cart-item-price">$${item.price.toFixed(2)}</div>
                            <div class="cart-item-actions">
                                <div class="cart-item-qty">
                                    <button class="cart-item-qty-btn" onclick="modifyQty(${item.id}, -1)">-</button>
                                    <span class="cart-item-qty-val">${item.qty}</span>
                                    <button class="cart-item-qty-btn" onclick="modifyQty(${item.id}, 1)">+</button>
                                </div>
                                <button class="cart-item-remove-btn" onclick="removeFromCart(${item.id})">Remove</button>
                            </div>
                        </div>
                    </div>
                `;
            });
            drawerContainer.innerHTML = itemsHtml;
            
            document.getElementById('cart-drawer-subtotal').textContent = `$${data.subtotal.toFixed(2)}`;
            document.getElementById('cart-drawer-total').textContent = `$${data.total.toFixed(2)}`;
            
            const checkoutBtn = document.getElementById('cart-checkout-btn');
            if (checkoutBtn) checkoutBtn.disabled = false;

            // Also check if we are on the Checkout or Cart pages, update tables if elements exist
            updatePageCartSummary(data);
        }
    })
    .catch(err => console.error("Error fetching cart items:", err));
}

// Function to update fields on specific pages (like checkout page summary)
function updatePageCartSummary(data) {
    const checkoutSummary = document.getElementById('checkout-items-summary');
    if (checkoutSummary) {
        let summaryHtml = '';
        data.items.forEach(item => {
            summaryHtml += `
                <div class="checkout-item">
                    <span class="checkout-item-name">${item.name} x${item.qty}</span>
                    <span class="checkout-item-total">$${(item.price * item.qty).toFixed(2)}</span>
                </div>
            `;
        });
        checkoutSummary.innerHTML = summaryHtml;
        
        const summarySub = document.getElementById('checkout-subtotal');
        const summaryTotal = document.getElementById('checkout-total');
        if (summarySub) summarySub.textContent = `$${data.subtotal.toFixed(2)}`;
        if (summaryTotal) {
            let total = data.total;
            if (window.activeDiscountPercent) {
                total = total * (1 - window.activeDiscountPercent);
            }
            summaryTotal.textContent = `$${total.toFixed(2)}`;
        }
    }
}

// Initial UI updates on page load
document.addEventListener('DOMContentLoaded', () => {
    updateCartUI();
});
