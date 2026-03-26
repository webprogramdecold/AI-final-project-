#!/usr/bin/env python3
"""
Test all API endpoints for AI Trading Analytics.

Calls unauthenticated and authenticated endpoints; verifies status codes.
Requires running app. Run from project root.
"""

import sys
import requests
import json
from typing import Dict, List, Tuple

BASE_URL = "http://localhost:5002"  # match port in app.py

# Colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
ENDC = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*70}{ENDC}")
    print(f"{BLUE}{text}{ENDC}")
    print(f"{BLUE}{'='*70}{ENDC}\n")

def print_test(endpoint, method, status_code, expected, passed, response_data=None):
    status_color = GREEN if passed else RED
    status_text = "✅ PASS" if passed else "❌ FAIL"
    
    print(f"{status_color}{status_text}{ENDC} | {method:6} {endpoint:40} | Status: {status_code} (expected: {expected})")
    
    if not passed and response_data:
        print(f"       Response: {json.dumps(response_data, indent=2)}")

def check_server_running():
    """Verify Flask app is reachable; exit with 1 if not."""
    try:
        requests.get(BASE_URL + "/", timeout=2)
    except requests.exceptions.RequestException:
        print(f"\n{RED}❌ Cannot connect to {BASE_URL}{ENDC}")
        print("   Start the Flask app first: python3 app.py\n")
        sys.exit(1)


def test_unauthenticated_endpoints():
    """Test endpoints that don't require authentication"""
    print_header("Testing Unauthenticated Endpoints")
    
    tests = [
        ("GET", "/", [200, 302, 303], "Home page redirect"),
        ("GET", "/login", [200], "Login page"),
        ("GET", "/register", [200], "Register page"),
    ]
    
    results = []
    for method, endpoint, expected_codes, description in tests:
        try:
            resp = requests.request(method, BASE_URL + endpoint, allow_redirects=False)
            passed = resp.status_code in expected_codes
            print_test(endpoint, method, resp.status_code, expected_codes, passed)
            results.append((endpoint, passed))
        except Exception as e:
            print(f"{RED}❌ ERROR{ENDC} | {method:6} {endpoint:40} | Exception: {str(e)}")
            results.append((endpoint, False))
    
    return results

def test_authenticated_endpoints(session):
    """Test endpoints that require authentication"""
    print_header("Testing Authenticated Endpoints")
    
    tests = [
        ("GET", "/dashboard", [200], "Dashboard page"),
        ("GET", "/api/price/BTCUSDT", [200, 404], "Get BTC price"),
        ("GET", "/api/price/ETHUSDT", [200, 404], "Get ETH price"),
        ("GET", "/api/exchange/accounts", [200], "List exchange accounts"),
        ("GET", "/api/fear_greed", [200, 500], "Fear & Greed index"),
    ]
    
    results = []
    for method, endpoint, expected_codes, description in tests:
        try:
            resp = session.request(method, BASE_URL + endpoint)
            passed = resp.status_code in expected_codes
            
            # Check for anti-pattern: HTTP 200 with success: false
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    if isinstance(data, dict) and data.get('success') == False:
                        print(f"{YELLOW}⚠️  WARNING{ENDC} | {method:6} {endpoint:40} | HTTP 200 with success: false")
                        print(f"       This is an anti-pattern. Should use 4xx/5xx status code.")
                        print(f"       Response: {json.dumps(data, indent=2)[:200]}...")
                        passed = False
                except Exception:
                    pass
            
            print_test(endpoint, method, resp.status_code, expected_codes, passed)
            results.append((endpoint, passed))
        except Exception as e:
            print(f"{RED}❌ ERROR{ENDC} | {method:6} {endpoint:40} | Exception: {str(e)}")
            results.append((endpoint, False))
    
    return results

def test_error_responses(session):
    """Test that error cases return proper HTTP status codes"""
    print_header("Testing Error Response Codes")
    
    tests = [
        ("GET", "/api/price/INVALIDXXX", [404, 500], "Invalid symbol"),
        ("POST", "/api/exchange/test_connection", [400, 500], "Test connection without data"),
    ]
    
    results = []
    for method, endpoint, expected_codes, description in tests:
        try:
            if method == "POST":
                resp = session.request(method, BASE_URL + endpoint, json={})
            else:
                resp = session.request(method, BASE_URL + endpoint)
            
            passed = resp.status_code in expected_codes
            
            # This is the key check: errors should NOT return 200
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    if isinstance(data, dict) and data.get('success') == False:
                        print(f"{RED}❌ ANTI-PATTERN DETECTED{ENDC}")
                        print(f"       {method:6} {endpoint}")
                        print(f"       Returned HTTP 200 with success: false")
                        print(f"       Should return {expected_codes[0]} instead")
                        print(f"       Response: {json.dumps(data, indent=2)}")
                        passed = False
                except Exception:
                    pass
            
            print_test(endpoint, method, resp.status_code, expected_codes, passed)
            results.append((endpoint, passed))
        except Exception as e:
            print(f"{RED}❌ ERROR{ENDC} | {method:6} {endpoint:40} | Exception: {str(e)}")
            results.append((endpoint, False))
    
    return results

def login(username="testuser", password="password123"):
    """Login and return session"""
    session = requests.Session()
    
    # Try to login
    resp = session.post(
        BASE_URL + "/login",
        data={"username": username, "password": password},
        allow_redirects=False
    )
    
    if resp.status_code in [200, 302, 303]:
        print(f"{GREEN}✅ Login successful{ENDC} (user: {username})")
        return session
    else:
        print(f"{YELLOW}⚠️  Login failed, trying to register...{ENDC}")
        
        # Try to register
        resp = session.post(
            BASE_URL + "/register",
            data={"username": username, "password": password},
            allow_redirects=False
        )
        
        if resp.status_code in [200, 302, 303]:
            print(f"{GREEN}✅ Registration successful{ENDC} (user: {username})")
            
            # Now login
            resp = session.post(
                BASE_URL + "/login",
                data={"username": username, "password": password},
                allow_redirects=False
            )
            
            if resp.status_code in [200, 302, 303]:
                print(f"{GREEN}✅ Login successful{ENDC} (user: {username})")
                return session
        
        print(f"{RED}❌ Could not login or register{ENDC}")
        return None

def main():
    print(f"\n{BLUE}{'='*70}{ENDC}")
    print(f"{BLUE}API ENDPOINT TEST SUITE{ENDC}")
    print(f"{BLUE}{'='*70}{ENDC}")
    print(f"\nTesting server: {BASE_URL}")
    print(f"Purpose: Verify all endpoints return correct HTTP status codes")
    print(f"Focus: Finding HTTP 200 responses with 'success: false' (anti-pattern)\n")

    check_server_running()

    # Test unauthenticated endpoints
    unauth_results = test_unauthenticated_endpoints()
    
    # Login
    print_header("Authentication")
    session = login()
    
    if session:
        # Test authenticated endpoints
        auth_results = test_authenticated_endpoints(session)
        
        # Test error responses
        error_results = test_error_responses(session)
        
        # Summary
        print_header("Test Summary")
        all_results = unauth_results + auth_results + error_results
        total = len(all_results)
        passed = sum(1 for _, p in all_results if p)
        failed = total - passed
        
        print(f"Total tests: {total}")
        print(f"{GREEN}Passed: {passed}{ENDC}")
        print(f"{RED}Failed: {failed}{ENDC}")
        
        if failed == 0:
            print(f"\n{GREEN}{'='*70}")
            print(f"🎉 ALL TESTS PASSED! No HTTP 200 with error messages found.")
            print(f"{'='*70}{ENDC}\n")
        else:
            print(f"\n{RED}{'='*70}")
            print(f"⚠️  SOME TESTS FAILED - Review output above for details")
            print(f"{'='*70}{ENDC}\n")
            sys.exit(1)
    else:
        print(f"\n{RED}Could not authenticate - skipping authenticated tests{ENDC}\n")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Test interrupted by user{ENDC}\n")
    except Exception as e:
        print(f"\n{RED}Fatal error: {e}{ENDC}\n")

