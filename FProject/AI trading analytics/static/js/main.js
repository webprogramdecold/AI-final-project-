/**
 * Shared client-side logic for AI Trading Analytics.
 * Notifications (showNotification, createNotificationContainer) and formatting
 * (formatCurrency, formatPercentage, formatNumber). Loaded from base template;
 * dashboard and other pages may rely on these.
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('AI Trading Analytics - JavaScript loaded');
});

function showNotification(message, type = 'info') {
    // Get or create container
    let container = document.querySelector('.flash-container');
    if (!container) container = createNotificationContainer();
    if (!container) return;
    
    // Remove all existing notifications first (only show one at a time)
    const existingNotifications = container.querySelectorAll('.notification');
    existingNotifications.forEach(notif => {
        notif.remove();
    });
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <span>${message}</span>
        <button class="notification-close" onclick="this.parentElement.remove()">×</button>
    `;
    
    // Add to flash container
    container.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

function createNotificationContainer() {
    const mainContent = document.querySelector('.main-content');
    if (!mainContent) return null;
    const container = document.createElement('div');
    container.className = 'flash-container';
    mainContent.insertBefore(container, mainContent.firstChild);
    return container;
}


function formatCurrency(value) {
    return '$' + value.toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

function formatPercentage(value) {
    const sign = value >= 0 ? '+' : '';
    return sign + value.toFixed(2) + '%';
}

function formatNumber(value) {
    if (value >= 1000000) {
        return (value / 1000000).toFixed(2) + 'M';
    } else if (value >= 1000) {
        return (value / 1000).toFixed(2) + 'K';
    }
    return value.toFixed(2);
}

