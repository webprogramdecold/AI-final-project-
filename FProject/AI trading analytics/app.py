"""
AI Trading Analytics – Flask entry point.

Paper trading with AI price predictions: register, login, dashboard, predictions,
virtual trades, exchange links, profile. Uses models, services, utils, config.
"""

import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
from models import db
from models import user_model
from models import exchange_account_model
from models import advanced_prediction_model
from services import price_sync_service
from utils import validators
import config

_here = os.path.dirname(os.path.abspath(__file__))
_template_folder = os.path.join(_here, 'templates')
_static_folder = os.path.join(_here, 'static')
app = Flask(__name__, template_folder=_template_folder, static_folder=_static_folder)
app.config['SECRET_KEY'] = config.SECRET_KEY


def login_required(f):
    """Redirect to login with warning if user_id not in session; else run route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def home():
    """Redirect to dashboard if logged in, else to login."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    """GET: show registration form. POST: validate, check uniqueness, create user, redirect to login."""
    if request.method == 'GET':
        return render_template('register.html')
    username = validators.sanitize_string(request.form.get('username', ''), max_length=50)
    email = validators.sanitize_string(request.form.get('email', ''), max_length=100)
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')
    is_valid, error = validators.validate_username(username)
    if not is_valid:
        flash(error, 'danger')
        return render_template('register.html')
    is_valid, error = validators.validate_email(email)
    if not is_valid:
        flash(error, 'danger')
        return render_template('register.html')
    is_valid, error = validators.validate_password(password)
    if not is_valid:
        flash(error, 'danger')
        return render_template('register.html')
    
    if password != confirm_password:
        flash('Passwords do not match!', 'danger')
        return render_template('register.html')
    if user_model.check_username_exists(username):
        flash('Username already exists. Please choose another one.', 'danger')
        return render_template('register.html')
    if user_model.check_email_exists(email):
        flash('Email already registered. Please use another email or login.', 'danger')
        return render_template('register.html')
    user_id = user_model.create_user(username, email, password)
    if user_id:
        flash(f'Registration successful! Welcome {username}. Please log in.', 'success')
        return redirect(url_for('login'))
    flash('Registration failed. Please try again.', 'danger')
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """GET: show login form. POST: validate, authenticate, set session, redirect to dashboard or show error."""
    if request.method == 'GET':
        return render_template('login.html')
    username = validators.sanitize_string(request.form.get('username', ''), max_length=50)
    password = request.form.get('password', '')
    if not username or not password:
        flash('Both username and password are required!', 'danger')
        return render_template('login.html')
    if len(username) > 50 or len(password) > 128:
        flash('Invalid credentials.', 'danger')
        return render_template('login.html')
    user = user_model.authenticate_user(username, password)
    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        password = None
        flash(f'Welcome back, {user["username"]}!', 'success')
        return redirect(url_for('dashboard'))
    flash('Invalid username or password. Please try again.', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    """Clear session and redirect to login."""
    username = session.get('username', 'User')
    session.clear()
    flash(f'Goodbye, {username}! You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/api/profile/update', methods=['POST'])
@login_required
def api_profile_update():
    """POST: update username, email, or password (JSON). Requires current_password when changing password. Returns JSON."""
    try:
        user_id = session.get('user_id')
        data = request.get_json() or {}
        new_username = data.get('username', '').strip()
        new_email = data.get('email', '').strip()
        new_password = data.get('password', '').strip()
        current_password = data.get('current_password', '').strip()
        updated_fields = []
        errors = []
        if not any([new_username, new_email, new_password]):
            return jsonify({
                'success': False,
                'error': 'No fields to update. Provide username, email, or password.'
            }), 400
        
        if new_password and not current_password:
            return jsonify({
                'success': False,
                'error': 'Current password required when changing password.'
            }), 400
        
        if current_password or new_password:
            from models import user_model
            user = user_model.get_user_by_id(user_id)
            if not user:
                return jsonify({
                    'success': False,
                    'error': 'User not found.'
                }), 404
            
            # Verify current password
            if not user_model.verify_password(user['password_hash'], current_password):
                return jsonify({
                    'success': False,
                    'error': 'Current password is incorrect.'
                }), 401
        
        # Update username
        if new_username:
            is_valid, error = validators.validate_username(new_username)
            if not is_valid:
                errors.append(f"Username: {error}")
            else:
                # Check if username already exists (but not current user)
                query = "SELECT id FROM users WHERE username = ? AND id != ?"
                existing = db.fetch_one(query, (new_username, user_id))
                
                if existing:
                    errors.append("Username already taken")
                else:
                    # Update username
                    update_query = "UPDATE users SET username = ? WHERE id = ?"
                    db.execute_query(update_query, (new_username, user_id))
                    session['username'] = new_username  # Update session
                    updated_fields.append('username')
                    print(f"✅ Updated username to: {new_username}")
        
        # Update email
        if new_email:
            is_valid, error = validators.validate_email(new_email)
            if not is_valid:
                errors.append(f"Email: {error}")
            else:
                # Check if email already exists (but not current user)
                query = "SELECT id FROM users WHERE email = ? AND id != ?"
                existing = db.fetch_one(query, (new_email, user_id))
                
                if existing:
                    errors.append("Email already registered")
                else:
                    # Update email
                    update_query = "UPDATE users SET email = ? WHERE id = ?"
                    db.execute_query(update_query, (new_email, user_id))
                    updated_fields.append('email')
                    print(f"✅ Updated email to: {new_email}")
        
        # Update password
        if new_password:
            is_valid, error = validators.validate_password(new_password)
            if not is_valid:
                errors.append(f"Password: {error}")
            else:
                # Hash new password (same method as user_model for consistency)
                from werkzeug.security import generate_password_hash
                hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
                
                # Update password
                update_query = "UPDATE users SET password_hash = ? WHERE id = ?"
                db.execute_query(update_query, (hashed_password, user_id))
                updated_fields.append('password')
                print(f"✅ Updated password")
        
        # Check for errors
        if errors:
            print(f"\n❌ Validation errors:")
            for error in errors:
                print(f"   - {error}")
            print(f"{'='*70}\n")
            
            return jsonify({
                'success': False,
                'errors': errors
            }), 400
        
        # Success
        print(f"\n✅ Profile updated successfully")
        print(f"   Updated fields: {', '.join(updated_fields)}")
        print(f"{'='*70}\n")
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'updated_fields': updated_fields
        }), 200
        
    except Exception as e:
        print(f"❌ Error updating profile: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================
# PROTECTED ROUTES (Login required)
# ============================================

@app.route('/dashboard')
@login_required
def dashboard():
    """Render main dashboard (user, active_symbol from session)."""
    user = user_model.get_user_by_id(session['user_id'])
    if not user:
        session.clear()
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('login'))
    active_symbol = session.get('active_symbol', 'BTCUSDT')
    return render_template('dashboard.html', user=user, active_symbol=active_symbol)


@app.route('/portfolio')
@login_required
def portfolio():
    """Render portfolio page (exchange accounts)."""
    user = user_model.get_user_by_id(session['user_id'])
    if not user:
        session.clear()
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('login'))
    
    return render_template('portfolio.html', user=user)


@app.route('/profile')
@login_required
def profile():
    """Render profile page (username, email)."""
    user_row = user_model.get_user_by_id(session['user_id'])
    if not user_row:
        session.clear()
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('login'))
    # Pass only profile-needed fields (no created_at, no balance / stats)
    user = {
        'id': user_row['id'],
        'username': user_row['username'],
        'email': user_row['email'],
    }
    return render_template('profile.html', user=user)


@app.route('/api/prediction/latest')
@app.route('/api/prediction/latest/<symbol>')
@login_required
def api_latest_prediction(symbol='BTCUSDT'):
    """GET: latest saved prediction for symbol. JSON: success, prediction or error."""
    try:
        user_id = session.get('user_id')
        prediction = advanced_prediction_model.get_latest_prediction_for_symbol(user_id, symbol)
        
        if prediction:
            return jsonify({
                'success': True,
                'prediction': prediction
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'No predictions found',
                'symbol': symbol
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/set_symbol', methods=['POST'])
@login_required
def api_set_symbol():
    """POST: save selected symbol in session. JSON body: symbol. Returns status/error."""
    try:
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        # Extract and validate symbol
        symbol = data.get('symbol', '').strip().upper()
        
        # Basic validation
        if not symbol:
            return jsonify({
                'status': 'error',
                'error': 'Symbol is required'
            }), 400
        
        # Validate symbol format (alphanumeric only)
        if not symbol.replace('_', '').isalnum():
            return jsonify({
                'status': 'error',
                'error': 'Invalid symbol format'
            }), 400
        
        # Save symbol in session
        # This maintains user's preference across page loads
        session['active_symbol'] = symbol
        
        print(f"✅ User {session['username']} selected symbol: {symbol}")
        
        # Return success
        return jsonify({
            'status': 'ok',
            'symbol': symbol,
            'message': f'Symbol updated to {symbol}'
        }), 200
        
    except Exception as e:
        print(f"Error setting symbol: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/price/<symbol>')
@login_required
def api_get_price(symbol):
    """GET: return current real-time price for symbol (realtime_price_service). JSON: success, symbol, price, formatted."""
    try:
        from services import realtime_price_service
        
        symbol = symbol.upper()
        
        # Get REAL-TIME price from exchange via CCXT
        # This replaces database lookups and dummy prices with LIVE market data
        price = realtime_price_service.get_current_price(symbol)
        
        if price and price > 0:
            return jsonify({
                'success': True,
                'symbol': symbol,
                'price': price,
                'formatted': f'${price:,.2f}'
            }), 200
        else:
            return jsonify({
                'success': False,
                'symbol': symbol,
                'error': 'Unable to fetch current price',
                'price': 0
            }), 404
            
    except Exception as e:
        print(f"Error getting real-time price: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'price': 0
        }), 500


@app.route('/exchanges')
@login_required
def exchanges():
    """Render exchanges page (linked accounts, user)."""
    user_id = session['user_id']
    accounts = exchange_account_model.get_exchange_accounts_for_user(user_id)
    user = user_model.get_user_by_id(user_id)
    return render_template('exchanges.html', accounts=accounts, user=user)


@app.route('/exchanges/add', methods=['POST'])
@login_required
def add_exchange():
    """POST: add exchange account (exchange_name, api_key, api_secret, etc.). Redirect to exchanges."""
    user_id = session['user_id']
    exchange_name = request.form.get('exchange_name', '').strip().lower()
    account_label = request.form.get('account_label', '').strip()
    api_key = request.form.get('api_key', '').strip()
    api_secret = request.form.get('api_secret', '').strip()
    is_testnet = request.form.get('is_testnet') == 'on'
    
    # Validation
    if not exchange_name or not api_key or not api_secret:
        flash('Exchange name, API key, and API secret are required!', 'danger')
        return redirect(url_for('exchanges'))
    
    if not account_label:
        account_label = f"{exchange_name.capitalize()} Account"
    
    # Create exchange account
    result = exchange_account_model.create_exchange_account(
        user_id=user_id,
        exchange_name=exchange_name,
        account_label=account_label,
        api_key=api_key,
        api_secret=api_secret,
        is_testnet=is_testnet
    )
    
    if result['success']:
        mode = "Testnet" if is_testnet else "Live"
        flash(f'✅ {exchange_name.capitalize()} account "{account_label}" linked successfully! ({mode} mode)', 'success')
    else:
        flash(f'❌ Failed to link account: {result["error"]}', 'danger')
    
    return redirect(url_for('exchanges'))


@app.route('/exchanges/<int:account_id>/delete', methods=['POST'])
@login_required
def delete_exchange(account_id):
    """POST: soft-delete exchange account (is_active=0). Redirect to exchanges."""
    user_id = session['user_id']
    result = exchange_account_model.delete_exchange_account(account_id, user_id)
    
    if result['success']:
        flash('✅ Exchange account removed successfully!', 'success')
    else:
        flash(f'❌ Failed to remove account: {result["error"]}', 'danger')
    
    return redirect(url_for('exchanges'))


@app.route('/faq')
def faq():
    """GET: render FAQ page (public)."""
    return render_template('faq.html')


@app.route('/privacy')
def privacy():
    """GET: render privacy policy page (public). Review for production use."""
    return render_template('privacy.html')


@app.route('/terms')
def terms():
    """GET: render terms of use page (public). Review for production use."""
    return render_template('terms.html')


@app.route('/api/exchange/accounts')
@login_required
def api_list_exchange_accounts():
    """GET: list linked exchange accounts for user (no secrets). JSON: success, accounts, count."""
    try:
        user_id = session['user_id']
        
        # Get user's exchange accounts
        accounts = exchange_account_model.get_exchange_accounts_for_user(user_id, active_only=True)
        
        return jsonify({
            'success': True,
            'accounts': accounts,
            'count': len(accounts)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/exchange/test_connection', methods=['POST'])
@login_required
def api_test_exchange_connection():
    """POST: test exchange connection (credentials or account_id). Returns JSON ok, exchange, message, balances_sample."""
    try:
        user_id = session['user_id']
        data = request.get_json() or {}
        from services import exchange_service
        if 'exchange' in data and 'api_key' in data and 'api_secret' in data:
            exchange_name = data.get('exchange', '').lower()
            api_key = data.get('api_key', '')
            api_secret = data.get('api_secret', '')
            is_testnet = bool(data.get('is_testnet', False))
            result = exchange_service.test_exchange_connection(
                exchange_name, 
                api_key, 
                api_secret, 
                is_testnet
            )
            
            return jsonify(result), 200 if result['ok'] else 400
        elif 'account_id' in data:
            account_id = data.get('account_id')
            account = exchange_account_model.get_exchange_account_by_id(account_id)
            
            if not account:
                return jsonify({
                    'ok': False,
                    'message': 'Exchange account not found',
                    'error_type': 'not_found'
                }), 404
            
            if account['user_id'] != user_id:
                return jsonify({
                    'ok': False,
                    'message': 'Unauthorized - account belongs to another user',
                    'error_type': 'unauthorized'
                }), 403
            result = exchange_service.test_exchange_connection(
                account['exchange_name'],
                account['api_key'],
                account['api_secret_encrypted'],
                bool(account.get('is_testnet', 0))
            )
            
            return jsonify(result), 200 if result['ok'] else 400
        
        else:
            return jsonify({
                'ok': False,
                'message': 'Missing required fields',
                'error': 'Provide either (exchange, api_key, api_secret) or (account_id)',
                'error_type': 'validation'
            }), 400
        
    except Exception as e:
        return jsonify({
            'ok': False,
            'message': 'Server error during connection test',
            'error': str(e),
            'error_type': 'server_error'
        }), 500


@app.route('/api/exchange/<int:account_id>/portfolio')
@login_required
def api_exchange_portfolio(account_id):
    """GET: fetch balances and positions for linked exchange account. JSON: success, exchange, balances, positions."""
    try:
        user_id = session['user_id']
        account = exchange_account_model.get_exchange_account_by_id(account_id, user_id)
        
        if not account:
            return jsonify({
                'success': False,
                'error': 'Exchange account not found or access denied'
            }), 404
        
        # Create exchange client using ccxt
        from services import exchange_client
        
        client = exchange_client.create_exchange_client(
            exchange_name=account['exchange_name'],
            api_key=account['api_key'],
            api_secret=account['api_secret'],  # Decoded in get_exchange_account_by_id()
            is_testnet=bool(account['is_testnet'])
        )
        
        if not client:
            return jsonify({
                'success': False,
                'error': f'Failed to create {account["exchange_name"]} client'
            }), 500
        
        # Fetch balances from exchange
        balances_dict = exchange_client.get_balances(client)
        
        # Format balances for frontend (filter out zero balances)
        balances = []
        if balances_dict:
            for asset, balance_info in balances_dict.items():
                if balance_info['total'] > 0:
                    balances.append({
                        'asset': asset,
                        'free': balance_info['free'],
                        'used': balance_info['used'],
                        'total': balance_info['total']
                    })
        
        # Fetch open positions (if exchange supports futures)
        positions = exchange_client.get_open_positions(client)
        
        # Format positions for frontend
        if not positions:
            positions = []
        
        # Return data
        return jsonify({
            'success': True,
            'exchange': account['exchange_name'],
            'account_label': account['account_label'],
            'is_testnet': bool(account['is_testnet']),
            'balances': balances,
            'positions': positions,
            'balance_count': len(balances),
            'position_count': len(positions)
        }), 200
        
    except Exception as e:
        print(f"Error fetching exchange portfolio: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to fetch data from exchange. Check API credentials and exchange status.'
        }), 500


@app.route('/api/prices/sync', methods=['POST'])
@login_required
def api_prices_sync():
    '''Sync price history from exchange. POST with symbol, timeframe, limit.'''
    try:
        # Get parameters
        if request.is_json:
            data = request.get_json()
        else:
            return jsonify({'success': False, 'error': 'Request must be JSON'}), 400
        
        symbol = data.get('symbol', '').strip().upper()
        timeframe = data.get('timeframe', '1h')
        limit = int(data.get('limit', 200))
        
        # Validation
        if not symbol:
            return jsonify({'success': False, 'error': 'Symbol required'}), 400
        
        # Sync prices
        result = price_sync_service.sync_price_history_for_symbol(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            exchange_name='binance'
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        print(f"Error syncing prices: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/advanced_prediction')
@login_required
def advanced_prediction_page():
    '''Advanced Prediction Page - AI predictions'''
    return render_template('advanced_prediction.html')


@app.route('/api/advanced_predict', methods=['POST'])
@login_required
def api_advanced_predict():
    '''Run advanced prediction with trained ML model (advanced_ai_predictor).'''
    try:
        from services import advanced_ai_predictor
        from models import advanced_prediction_model
        
        data = request.get_json() or {}
        symbol = data.get('symbol', 'BTC/USDT')
        timeframe = data.get('timeframe', '1h')
        
        result = advanced_ai_predictor.advanced_ai_predict(symbol, timeframe)
        
        if result.get('error'):
            return jsonify({
                'success': False,
                'error': result.get('error', 'Prediction failed'),
                'details': result.get('summary', result.get('error'))
            }), 400
        
        if 'target_price' not in result:
            return jsonify({
                'success': False,
                'error': 'Prediction failed: ' + result.get('error', 'Unknown error'),
                'details': result.get('summary', 'No details available')
            }), 400
        
        # Save to database
        user_id = session.get('user_id')
        pred_id = advanced_prediction_model.save_prediction(user_id, symbol, timeframe, result)
        result['prediction_id'] = pred_id
        result['success'] = True
        
        return jsonify(result), 200
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in advanced_predict: {e}")
        print(error_details)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/prediction_history', methods=['GET'])
@login_required
def api_prediction_history():
    '''Get user prediction history.'''
    try:
        from models import advanced_prediction_model
        user_id = session.get('user_id')
        predictions = advanced_prediction_model.get_user_predictions(user_id, limit=20)
        performance = advanced_prediction_model.get_prediction_performance(user_id)
        return jsonify({'success': True, 'predictions': predictions, 'performance': performance}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/fear_greed')
@login_required
def api_fear_greed():
    '''Get Crypto Fear & Greed Index. GET /api/fear_greed.'''
    try:
        # Import market data service
        from services import market_data_service
        
        print(f"\n{'='*60}")
        print(f"API REQUEST: Fear & Greed Index")
        print(f"User ID: {session.get('user_id')}")
        print(f"{'='*60}")
        
        # Call service to get Fear & Greed Index
        result = market_data_service.get_fear_greed_index()
        
        if result.get('success'):
            print(f"✅ Fear & Greed Index: {result['value']}/100 ({result['value_classification']})")
        else:
            print(f"❌ Failed to fetch Fear & Greed Index: {result.get('error')}")
        
        print(f"{'='*60}\n")
        
        # Return result directly (service already returns proper format)
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Error in api_fear_greed: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/market/top')
@login_required
def api_market_top():
    '''Get top cryptocurrencies by market cap. GET /api/market/top?limit=100'''
    try:
        # Import market data service
        from services import market_data_service
        
        # Get limit from query parameters (default: 100)
        limit = request.args.get('limit', 100, type=int)
        
        # Validate limit
        if limit < 1:
            limit = 1
        elif limit > 5000:
            limit = 5000
        
        print(f"\n{'='*60}")
        print(f"API REQUEST: Top {limit} Cryptocurrencies")
        print(f"User ID: {session.get('user_id')}")
        print(f"{'='*60}")
        
        # Call service to get top coins
        result = market_data_service.get_top_coins(limit=limit)
        
        if result.get('data'):
            print(f"✅ Fetched {len(result['data'])} cryptocurrencies")
            if result.get('demo_mode'):
                print(f"   📝 Using demo data (CoinMarketCap API key not configured)")
            else:
                print(f"   🌐 Using real data from CoinMarketCap API")
        else:
            print(f"❌ Failed to fetch top coins: {result.get('error')}")
        
        print(f"{'='*60}\n")
        
        # Return result directly (service already returns proper format)
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Error in api_market_top: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/market/live_prices')
@login_required
def api_market_live_prices():
    '''Get live prices for symbols. GET /api/market/live_prices?symbols=BTC,ETH,BNB'''
    try:
        from services import market_data_service
        
        # Get symbols from query parameter
        symbols_param = request.args.get('symbols', 'BTC,ETH,BNB,SOL,XRP')
        symbols = [s.strip().upper() for s in symbols_param.split(',')]
        
        # Get live prices
        result = market_data_service.get_live_prices(symbols)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Error in api_market_live_prices: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/market/token/<symbol>')
@login_required
def api_market_token_details(symbol):
    '''Get detailed token information. GET /api/market/token/BTC.'''
    try:
        from services import market_data_service
        
        symbol = symbol.upper().strip()
        
        # Get detailed token information
        result = market_data_service.get_token_details(symbol)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Error in api_market_token_details: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/db_overview')
@login_required
def api_db_overview():
    '''Database overview. GET /api/db_overview. Returns table counts and size info.'''
    try:
        from services import db_diagnostics
        
        print(f"\n{'='*70}")
        print(f"DATABASE OVERVIEW REQUEST")
        print(f"User ID: {session.get('user_id')}")
        print(f"{'='*70}")
        
        # Get database overview
        overview = db_diagnostics.get_db_overview()
        
        # Get database size info
        size_info = db_diagnostics.get_database_size_info()
        
        # Calculate total records
        total_records = sum(count for count in overview.values() if count > 0)
        
        print(f"\n📊 Database Statistics:")
        print(f"   Total Tables: {len(overview)}")
        print(f"   Total Records: {total_records:,}")
        print(f"   Database Size: {size_info.get('total_size_readable', 'Unknown')}")
        print(f"{'='*70}\n")
        
        return jsonify({
            'success': True,
            'overview': overview,
            'total_records': total_records,
            'size_info': {
                'total_size_readable': size_info.get('total_size_readable', 'Unknown'),
                'total_size_mb': size_info.get('total_size_mb', 0)
            }
        }), 200
        
    except Exception as e:
        print(f"❌ Error getting database overview: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/health')
def api_health():
    '''Health check endpoint. GET /api/health. Returns db, price_service, data_service status.'''
    from datetime import datetime
    import traceback
    
    checks = {}
    details = {}
    overall_status = "ok"
    
    # ========================================
    # Check 1: Database Connectivity
    # ========================================
    try:
        # Simple query to verify DB connection
        result = db.fetch_one("SELECT 1 as health_check")
        checks['db'] = (result is not None)
        if not checks['db']:
            details['db_error'] = "Database query returned None"
            overall_status = "degraded"
    except Exception as e:
        checks['db'] = False
        details['db_error'] = str(e)
        overall_status = "degraded"
        print(f"❌ Health Check - DB failed: {e}")
    
    # ========================================
    # Check 2: Price Service
    # ========================================
    try:
        # Try to fetch a real price for BTC (returns float, not dict)
        from services.realtime_price_service import get_current_price
        price_result = get_current_price("BTCUSDT")
        
        if isinstance(price_result, (int, float)) and price_result > 0:
            checks['price_service'] = True
        else:
            checks['price_service'] = False
            details['price_error'] = 'No valid price returned'
            overall_status = "degraded"
    except Exception as e:
        checks['price_service'] = False
        details['price_error'] = str(e)
        overall_status = "degraded"
        print(f"❌ Health Check - Price Service failed: {e}")
    
    # ========================================
    # Check 3: Data Service (OHLCV for predictions)
    # ========================================
    try:
        from services.advanced_data_service import AdvancedDataService
        data_service = AdvancedDataService()
        df = data_service.get_ohlcv("BTCUSDT", "1h", limit=50)
        if df is not None and len(df) >= 20:
            checks['data_service'] = True
        else:
            checks['data_service'] = False
            details['data_error'] = 'Insufficient data for prediction'
            overall_status = "degraded"
    except Exception as e:
        checks['data_service'] = False
        details['data_error'] = str(e)
        overall_status = "degraded"
        print(f"❌ Health Check - Data Service failed: {e}")
    
    # ========================================
    # Build Response
    # ========================================
    
    # If all checks passed, status is "ok"
    # If some failed, status is "degraded" (still responding)
    # If critical failure, status is "error"
    
    response = {
        "status": overall_status,
        "version": "0.1.0",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "checks": checks
    }
    
    # Only include details if there are errors
    if details:
        response['details'] = details
    
    # Log the health check result
    passed = sum(checks.values())
    total = len(checks)
    print(f"🏥 Health Check: {passed}/{total} checks passed - Status: {overall_status}")
    
    # Return 200 even if degraded (service is still running)
    # Return 500 only if critical failure
    status_code = 200 if overall_status in ["ok", "degraded"] else 500
    
    return jsonify(response), status_code


if __name__ == "__main__":
    login_html = os.path.join(_template_folder, 'login.html')
    if not os.path.isfile(login_html):
        print("ERROR: templates not found. Run this app from the AI trading analytics folder (the one that contains app.py and templates/).")
        print("  Expected templates at:", _template_folder)
        print("  Current app.py at:   ", _here)
        exit(1)
    port = 5002
    print("\n  Open in browser: http://127.0.0.1:{}/\n".format(port))
    app.run(debug=True, host='127.0.0.1', port=port)

