// Global Frontend Utilities and Page Logic

// Open Cart Drawer
function openCartDrawer() {
    const drawer = document.getElementById('cart-drawer');
    const overlay = document.getElementById('cart-drawer-overlay');
    if (drawer && overlay) {
        drawer.classList.add('active');
        overlay.classList.add('active');
        document.body.style.overflow = 'hidden'; // Lock background scroll
    }
}

// Close Cart Drawer
function closeCartDrawer() {
    const drawer = document.getElementById('cart-drawer');
    const overlay = document.getElementById('cart-drawer-overlay');
    if (drawer && overlay) {
        drawer.classList.remove('active');
        overlay.classList.remove('active');
        document.body.style.overflow = ''; // Unlock scroll
    }
}

// Custom Toast Alerts
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type} glass-panel`;
    
    let iconSvg = '';
    if (type === 'success') {
        iconSvg = `<svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>`;
    } else {
        iconSvg = `<svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>`;
    }
    
    toast.innerHTML = `
        ${iconSvg}
        <span>${message}</span>
    `;
    
    container.appendChild(toast);
    
    // Auto remove toast after 3.5 seconds
    setTimeout(() => {
        toast.style.animation = 'fade-in 0.3s reverse forwards';
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 3500);
}

// Account Section Tab Switching
function switchAccountTab(tabName) {
    // Hide all panels
    const panels = document.querySelectorAll('.account-panel');
    panels.forEach(p => p.classList.remove('active'));
    
    // Deactivate all buttons
    const buttons = document.querySelectorAll('.account-nav-btn');
    buttons.forEach(b => b.classList.remove('active'));
    
    // Show target panel and active button
    const targetPanel = document.getElementById(`panel-${tabName}`);
    const targetButton = document.getElementById(`tab-btn-${tabName}`);
    if (targetPanel && targetButton) {
        targetPanel.classList.add('active');
        targetButton.classList.add('active');
    }
}

// Setup listeners
document.addEventListener('DOMContentLoaded', () => {
    // Add close listener for cart overlay
    const overlay = document.getElementById('cart-drawer-overlay');
    if (overlay) {
        overlay.addEventListener('click', closeCartDrawer);
    }
    
    // Handle Esc key to close drawers
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeCartDrawer();
            
            // Close Telegram mock modal if open
            const telOverlay = document.getElementById('telegram-modal-overlay');
            if (telOverlay) {
                closeTelegramModal();
            }
        }
    });
});

// Telegram notification modal controller (for debugging/visual feedback)
function closeTelegramModal() {
    const overlay = document.getElementById('telegram-modal-overlay');
    if (overlay) {
        overlay.style.opacity = '0';
        setTimeout(() => {
            overlay.remove();
        }, 300);
    }
}
