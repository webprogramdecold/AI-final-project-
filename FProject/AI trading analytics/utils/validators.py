"""
Input validation for AI Trading Analytics.

Validates email, username, password, trade data (symbol, side, quantity, price);
sanitizes strings; optional validate_quantity and validate_price helpers.
Used by app.py for registration, login, profile, and trade routes.
"""

import re


def validate_email(email):
    """Validate email format (required, max 100 chars, basic pattern). Returns (is_valid, error_message)."""
    if not email or not isinstance(email, str):
        return False, "Email is required"
    
    email = email.strip()
    
    if len(email) == 0:
        return False, "Email cannot be empty"
    
    if len(email) > 100:
        return False, "Email is too long (max 100 characters)"
    
    # Simple email pattern: something@something.something
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        return False, "Invalid email format (example: user@example.com)"
    
    return True, None


def validate_username(username):
    """Validate username (required, 3–50 chars, alphanumeric and underscore). Returns (is_valid, error_message)."""
    if not username or not isinstance(username, str):
        return False, "Username is required"
    
    username = username.strip()
    
    if len(username) == 0:
        return False, "Username cannot be empty"
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters long"
    
    if len(username) > 50:
        return False, "Username is too long (max 50 characters)"
    
    # Allow only alphanumeric characters and underscores
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Username can only contain letters, numbers, and underscores"
    
    return True, None


def validate_password(password):
    """Validate password (required, 6–128 chars). Returns (is_valid, error_message)."""
    if not password or not isinstance(password, str):
        return False, "Password is required"
    
    if len(password) == 0:
        return False, "Password cannot be empty"
    
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    
    if len(password) > 128:
        return False, "Password is too long (max 128 characters)"
    
    return True, None


def validate_trade_data(symbol, side, quantity, price):
    """Validate symbol, side (BUY/SELL), quantity, price. Returns (is_valid, error_message)."""
    if not symbol or not isinstance(symbol, str):
        return False, "Symbol is required"
    symbol = symbol.strip().upper()
    if len(symbol) == 0:
        return False, "Symbol cannot be empty"
    if len(symbol) > 20:
        return False, "Symbol is too long"
    if not re.match(r'^[A-Z0-9]+$', symbol):
        return False, "Invalid symbol format"
    
    if not side or not isinstance(side, str):
        return False, "Trade side is required (BUY or SELL)"
    
    side = side.strip().upper()
    
    if side not in ['BUY', 'SELL']:
        return False, "Trade side must be BUY or SELL"
    
    try:
        quantity = float(quantity)
    except (TypeError, ValueError):
        return False, "Quantity must be a valid number"
    
    if quantity <= 0:
        return False, "Quantity must be greater than 0"
    
    if quantity > 1000000:
        return False, "Quantity is too large"
    
    try:
        price = float(price)
    except (TypeError, ValueError):
        return False, "Price must be a valid number"
    
    if price <= 0:
        return False, "Price must be greater than 0"
    
    if price > 10000000:
        return False, "Price is too high"
    
    return True, None


def sanitize_string(input_str, max_length=100):
    """Strip whitespace, truncate to max_length, remove null bytes. Returns sanitized string."""
    if not input_str or not isinstance(input_str, str):
        return ""
    sanitized = input_str.strip()[:max_length].replace('\x00', '')
    
    return sanitized


def validate_quantity(quantity_str):
    """Convert quantity to float; must be in (0, 1000000]. Returns (is_valid, value, error)."""
    try:
        quantity = float(quantity_str)
        
        if quantity <= 0:
            return False, None, "Quantity must be greater than 0"
        
        if quantity > 1000000:
            return False, None, "Quantity is too large"
        
        return True, quantity, None
        
    except (TypeError, ValueError):
        return False, None, "Invalid quantity format"


def validate_price(price_str):
    """Convert price to float; must be in (0, 10000000]. Returns (is_valid, value, error)."""
    try:
        price = float(price_str)
        
        if price <= 0:
            return False, None, "Price must be greater than 0"
        
        if price > 10000000:
            return False, None, "Price is too high"
        
        return True, price, None
        
    except (TypeError, ValueError):
        return False, None, "Invalid price format"

