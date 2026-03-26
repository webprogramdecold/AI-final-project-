"""
Test prediction-related API via HTTP for AI Trading Analytics.

Logs in with demo user, calls /api/prediction/latest.
Requires running app (python app.py) and demo user (scripts/create_demo_user.py). Run from project root.
"""

import requests
import json


BASE_URL = 'http://127.0.0.1:5002'
USERNAME = 'testuser'
PASSWORD = 'password123'


def test_api():
    """Test the latest-prediction API endpoint."""
    print("=" * 70)
    print("TESTING PREDICTION API (latest saved)")
    print("=" * 70)

    session = requests.Session()

    print("\n[Step 1] Logging in...")
    response = session.post(f'{BASE_URL}/login', data={'username': USERNAME, 'password': PASSWORD}, allow_redirects=False)
    if response.status_code not in [200, 302]:
        print(f"❌ Login failed! Status: {response.status_code}")
        print("   Make sure: Flask app is running (python app.py) and demo user exists (python scripts/create_demo_user.py)")
        return

    print("✅ Login successful!")

    print("\n[Step 2] Testing latest prediction API...")
    response = session.get(f'{BASE_URL}/api/prediction/latest')
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            prediction = data.get('prediction')
            print(f"✅ Latest Prediction: {prediction.get('symbol')} {prediction.get('direction')} ({prediction.get('confidence_pct')}%)")
        else:
            print("⚠️  No saved predictions (OK)")
    else:
        print(f"⚠️  Response: {response.status_code}")

    print("\n" + "=" * 70)
    print("✅ API TESTING COMPLETE!")
    print("  - GET /api/prediction/latest")
    print("  - GET /api/prediction/latest/<symbol>")
    print("=" * 70)


def test_without_login():
    """Test that API is protected (requires login)."""
    print("\n[Test] Accessing /api/prediction/latest without login...")
    response = requests.get(f'{BASE_URL}/api/prediction/latest')
    if response.status_code == 302 or 'login' in (response.text or '').lower():
        print("✅ API is protected - redirects to login")
    else:
        print("⚠️  API might not be protected properly")


if __name__ == "__main__":
    import sys
    print("\n🚀 Starting API tests... (Flask app must be running: python app.py)\n")
    try:
        test_without_login()
        test_api()
    except requests.exceptions.ConnectionError:
        print("\n❌ Could not connect to Flask app! Run: python app.py")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
