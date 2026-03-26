-- MySQL schema for AI Trading Analytics.
-- Used by setup_database.py to create the database and base tables when using MySQL.
-- Default deployment uses SQLite; this file is for optional MySQL setup.

CREATE DATABASE IF NOT EXISTS ai_trading_db;
USE ai_trading_db;

-- Users: accounts, auth, and virtual balance for paper trading.
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    balance DECIMAL(15, 2) DEFAULT 10000.00,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email)
);

-- Historical OHLCV price data; used by charts and by the AI predictor for features.
CREATE TABLE price_history (
    id INT PRIMARY KEY AUTO_INCREMENT,
    symbol VARCHAR(20) NOT NULL,
    timestamp DATETIME NOT NULL,
    open_price DECIMAL(15, 2) NOT NULL,
    high_price DECIMAL(15, 2) NOT NULL,
    low_price DECIMAL(15, 2) NOT NULL,
    close_price DECIMAL(15, 2) NOT NULL,
    volume DECIMAL(20, 8) DEFAULT 0,
    INDEX idx_symbol_timestamp (symbol, timestamp),
    INDEX idx_timestamp (timestamp)
);

-- Legacy predictions table (simple UP/DOWN). Main app uses advanced_predictions (SQLite has full tables in scripts/setup_sqlite.py).
CREATE TABLE predictions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    symbol VARCHAR(20) NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    prediction_class TINYINT NOT NULL,
    confidence FLOAT NOT NULL,
    INDEX idx_symbol_timestamp (symbol, timestamp),
    CHECK (prediction_class IN (0, 1)),
    CHECK (confidence >= 0 AND confidence <= 1)
);

-- Per-user crypto holdings (paper trading): symbol, quantity, average price.
CREATE TABLE portfolio (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    quantity DECIMAL(20, 8) NOT NULL,
    average_price DECIMAL(15, 2) NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_symbol (user_id, symbol),
    INDEX idx_user_id (user_id),
    CHECK (quantity >= 0)
);

-- Paper trading history: buy/sell with quantity, price, total.
CREATE TABLE trades (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    side ENUM('BUY', 'SELL') NOT NULL,
    quantity DECIMAL(20, 8) NOT NULL,
    price DECIMAL(15, 2) NOT NULL,
    total_amount DECIMAL(15, 2) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at),
    INDEX idx_user_symbol (user_id, symbol),
    CHECK (quantity > 0),
    CHECK (price > 0)
);
