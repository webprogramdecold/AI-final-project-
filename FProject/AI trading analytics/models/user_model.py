"""
User accounts and authentication for AI Trading Analytics.

Handles registration (create_user, uniqueness checks), login (authenticate_user),
and profile data (get_user_by_id, update_user_balance). Passwords are hashed
with werkzeug (pbkdf2:sha256); plain-text passwords are never stored.

Used by: app.py (register, login, logout, profile, dashboard, portfolio, exchanges).
"""

from werkzeug.security import generate_password_hash, check_password_hash

from models import db


def create_user(username, email, password_plain):
    """
    Create a new user with a hashed password and default balance.

    Args:
        username: Unique username.
        email: User email (must be unique).
        password_plain: Plain-text password; it is hashed before storage.

    Returns:
        New user id on success, None on failure (e.g. duplicate username/email).
    """
    password_hash = generate_password_hash(password_plain, method='pbkdf2:sha256')
    query = """
        INSERT INTO users (username, email, password_hash, balance)
        VALUES (?, ?, ?, 10000.00)
    """
    params = (username, email, password_hash)
    user_id = db.execute_query(query, params)
    return user_id


def get_user_by_username(username):
    """
    Fetch a user by username (e.g. for login).

    Returns:
        Row as dict (id, username, email, password_hash, balance, created_at) or None.
    """
    query = "SELECT * FROM users WHERE username = ?"
    return db.fetch_one(query, (username,))


def get_user_by_id(user_id):
    """
    Fetch a user by id (e.g. from session after login).

    Returns:
        Row as dict or None.
    """
    query = "SELECT * FROM users WHERE id = ?"
    return db.fetch_one(query, (user_id,))


def verify_password(password_plain, password_hash):
    """
    Check that a plain-text password matches the stored hash.

    Returns:
        True if match, False otherwise.
    """
    return check_password_hash(password_hash, password_plain)


def authenticate_user(username, password):
    """
    Authenticate by username and password.

    Returns:
        User dict if valid, None otherwise.
    """
    user = get_user_by_username(username)
    if user is None:
        return None
    if verify_password(password, user['password_hash']):
        return user
    return None


def check_username_exists(username):
    """
    Check whether a username is already taken (for registration validation).

    Returns:
        True if exists, False otherwise.
    """
    return get_user_by_username(username) is not None


def check_email_exists(email):
    """
    Check whether an email is already registered (for registration validation).

    Returns:
        True if exists, False otherwise.
    """
    query = "SELECT id FROM users WHERE email = ?"
    row = db.fetch_one(query, (email,))
    return row is not None


def update_user_balance(user_id, new_balance):
    """
    Set a user's balance (e.g. after paper trades).

    Returns:
        True if the update succeeded, False otherwise.
    """
    query = "UPDATE users SET balance = ? WHERE id = ?"
    result = db.execute_query(query, (new_balance, user_id))
    return result is not None
