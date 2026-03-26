"""
Create a demo user for testing AI Trading Analytics.

Creates a user with username testuser and password password123 (email test@example.com).
If the user already exists, prints the credentials and exits. Run from project root:
  python3 scripts/create_demo_user.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import user_model

USERNAME = "testuser"
EMAIL = "test@example.com"
PASSWORD = "password123"


def main():
    if user_model.check_username_exists(USERNAME):
        print(f"User '{USERNAME}' already exists. Use: Username={USERNAME}, Password={PASSWORD}")
        return
    user_id = user_model.create_user(USERNAME, EMAIL, PASSWORD)
    if user_id:
        print(f"Demo user created. Username: {USERNAME}, Password: {PASSWORD}")
    else:
        print("Failed to create user (database not set up or email already registered).")


if __name__ == "__main__":
    main()
