"""Database models and schema for portfolio management."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
import pandas as pd


class PortfolioDB:
    """SQLite database for portfolio management."""
    
    def __init__(self, db_path: str = "portfolio.db"):
        """Initialize database connection."""
        self.db_path = db_path
        self.conn = None
        self.init_database()
    
    def init_database(self):
        """Create database tables if they don't exist."""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = self.conn.cursor()
        
        # Portfolio holdings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                shares REAL NOT NULL,
                avg_buy_price REAL NOT NULL,
                purchase_date TEXT NOT NULL,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Transaction history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                transaction_type TEXT NOT NULL,
                shares REAL NOT NULL,
                price REAL NOT NULL,
                total_value REAL NOT NULL,
                transaction_date TEXT NOT NULL,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Watchlist table (separate from portfolio)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT UNIQUE NOT NULL,
                added_date TEXT NOT NULL,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Trading signals history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS signal_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                signal_type TEXT NOT NULL,
                confidence REAL NOT NULL,
                entry_price REAL NOT NULL,
                target_price REAL NOT NULL,
                stop_loss REAL NOT NULL,
                reasoning TEXT,
                signal_date TEXT NOT NULL,
                status TEXT DEFAULT 'OPEN',
                closed_date TEXT,
                actual_exit_price REAL,
                profit_loss REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.commit()
    
    # Portfolio Management
    def add_position(self, symbol: str, shares: float, avg_buy_price: float, 
                    purchase_date: str = None, notes: str = "") -> int:
        """Add or update a portfolio position."""
        if purchase_date is None:
            purchase_date = datetime.now().strftime("%Y-%m-%d")
        
        cursor = self.conn.cursor()
        
        # Check if position already exists
        existing = self.get_position(symbol)
        
        if existing:
            # Update existing position (average price calculation)
            old_shares = existing['shares']
            old_price = existing['avg_buy_price']
            
            total_shares = old_shares + shares
            new_avg_price = ((old_shares * old_price) + (shares * avg_buy_price)) / total_shares
            
            cursor.execute("""
                UPDATE portfolio 
                SET shares = ?, avg_buy_price = ?, updated_at = ?
                WHERE symbol = ?
            """, (total_shares, new_avg_price, datetime.now().isoformat(), symbol))
            
            position_id = existing['id']
        else:
            # Insert new position
            cursor.execute("""
                INSERT INTO portfolio (symbol, shares, avg_buy_price, purchase_date, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (symbol, shares, avg_buy_price, purchase_date, notes))
            
            position_id = cursor.lastrowid
        
        # Record transaction
        self.add_transaction(symbol, "BUY", shares, avg_buy_price, purchase_date, notes)
        
        self.conn.commit()
        return position_id
    
    def sell_position(self, symbol: str, shares: float, sell_price: float,
                     transaction_date: str = None, notes: str = "") -> bool:
        """Sell shares from a position."""
        if transaction_date is None:
            transaction_date = datetime.now().strftime("%Y-%m-%d")
        
        cursor = self.conn.cursor()
        position = self.get_position(symbol)
        
        if not position:
            return False
        
        if shares > position['shares']:
            raise ValueError(f"Cannot sell {shares} shares. Only {position['shares']} available.")
        
        new_shares = position['shares'] - shares
        
        if new_shares <= 0:
            # Remove position entirely
            cursor.execute("DELETE FROM portfolio WHERE symbol = ?", (symbol,))
        else:
            # Update remaining shares
            cursor.execute("""
                UPDATE portfolio 
                SET shares = ?, updated_at = ?
                WHERE symbol = ?
            """, (new_shares, datetime.now().isoformat(), symbol))
        
        # Record transaction
        self.add_transaction(symbol, "SELL", shares, sell_price, transaction_date, notes)
        
        self.conn.commit()
        return True
    
    def get_position(self, symbol: str) -> Optional[Dict]:
        """Get a specific portfolio position."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, symbol, shares, avg_buy_price, purchase_date, notes, created_at, updated_at
            FROM portfolio WHERE symbol = ?
        """, (symbol,))
        
        row = cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'symbol': row[1],
                'shares': row[2],
                'avg_buy_price': row[3],
                'purchase_date': row[4],
                'notes': row[5],
                'created_at': row[6],
                'updated_at': row[7]
            }
        return None
    
    def get_all_positions(self) -> List[Dict]:
        """Get all portfolio positions."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, symbol, shares, avg_buy_price, purchase_date, notes, created_at, updated_at
            FROM portfolio ORDER BY symbol
        """)
        
        positions = []
        for row in cursor.fetchall():
            positions.append({
                'id': row[0],
                'symbol': row[1],
                'shares': row[2],
                'avg_buy_price': row[3],
                'purchase_date': row[4],
                'notes': row[5],
                'created_at': row[6],
                'updated_at': row[7]
            })
        
        return positions
    
    def get_portfolio_symbols(self) -> List[str]:
        """Get list of all symbols in portfolio."""
        positions = self.get_all_positions()
        return [p['symbol'] for p in positions]
    
    # Transaction Management
    def add_transaction(self, symbol: str, transaction_type: str, shares: float,
                       price: float, transaction_date: str = None, notes: str = "") -> int:
        """Add a transaction record."""
        if transaction_date is None:
            transaction_date = datetime.now().strftime("%Y-%m-%d")
        
        total_value = shares * price
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO transactions (symbol, transaction_type, shares, price, total_value, 
                                     transaction_date, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (symbol, transaction_type, shares, price, total_value, transaction_date, notes))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def get_transactions(self, symbol: str = None, limit: int = 100) -> List[Dict]:
        """Get transaction history."""
        cursor = self.conn.cursor()
        
        if symbol:
            cursor.execute("""
                SELECT id, symbol, transaction_type, shares, price, total_value, 
                       transaction_date, notes, created_at
                FROM transactions WHERE symbol = ?
                ORDER BY transaction_date DESC, created_at DESC
                LIMIT ?
            """, (symbol, limit))
        else:
            cursor.execute("""
                SELECT id, symbol, transaction_type, shares, price, total_value, 
                       transaction_date, notes, created_at
                FROM transactions
                ORDER BY transaction_date DESC, created_at DESC
                LIMIT ?
            """, (limit,))
        
        transactions = []
        for row in cursor.fetchall():
            transactions.append({
                'id': row[0],
                'symbol': row[1],
                'transaction_type': row[2],
                'shares': row[3],
                'price': row[4],
                'total_value': row[5],
                'transaction_date': row[6],
                'notes': row[7],
                'created_at': row[8]
            })
        
        return transactions
    
    # Signal History Management
    def save_signal(self, symbol: str, signal_type: str, confidence: float,
                   entry_price: float, target_price: float, stop_loss: float,
                   reasoning: str, signal_date: str = None) -> int:
        """Save a trading signal."""
        if signal_date is None:
            signal_date = datetime.now().strftime("%Y-%m-%d")
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO signal_history (symbol, signal_type, confidence, entry_price,
                                       target_price, stop_loss, reasoning, signal_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (symbol, signal_type, confidence, entry_price, target_price, stop_loss,
              reasoning, signal_date))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def close_signal(self, signal_id: int, actual_exit_price: float,
                    closed_date: str = None) -> bool:
        """Close a trading signal with actual results."""
        if closed_date is None:
            closed_date = datetime.now().strftime("%Y-%m-%d")
        
        cursor = self.conn.cursor()
        
        # Get the signal
        cursor.execute("""
            SELECT entry_price, signal_type FROM signal_history WHERE id = ?
        """, (signal_id,))
        
        row = cursor.fetchone()
        if not row:
            return False
        
        entry_price, signal_type = row
        
        # Calculate profit/loss
        if signal_type == "BUY":
            profit_loss = ((actual_exit_price - entry_price) / entry_price) * 100
        else:  # SELL
            profit_loss = ((entry_price - actual_exit_price) / entry_price) * 100
        
        # Update signal
        cursor.execute("""
            UPDATE signal_history
            SET status = 'CLOSED', closed_date = ?, actual_exit_price = ?, profit_loss = ?
            WHERE id = ?
        """, (closed_date, actual_exit_price, profit_loss, signal_id))
        
        self.conn.commit()
        return True
    
    def get_signals(self, symbol: str = None, status: str = None, limit: int = 50) -> List[Dict]:
        """Get trading signals."""
        cursor = self.conn.cursor()
        
        query = """
            SELECT id, symbol, signal_type, confidence, entry_price, target_price,
                   stop_loss, reasoning, signal_date, status, closed_date,
                   actual_exit_price, profit_loss, created_at
            FROM signal_history
            WHERE 1=1
        """
        params = []
        
        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY signal_date DESC, created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        
        signals = []
        for row in cursor.fetchall():
            signals.append({
                'id': row[0],
                'symbol': row[1],
                'signal_type': row[2],
                'confidence': row[3],
                'entry_price': row[4],
                'target_price': row[5],
                'stop_loss': row[6],
                'reasoning': row[7],
                'signal_date': row[8],
                'status': row[9],
                'closed_date': row[10],
                'actual_exit_price': row[11],
                'profit_loss': row[12],
                'created_at': row[13]
            })
        
        return signals
    
    # Analytics
    def get_portfolio_summary(self, current_prices: Dict[str, float]) -> Dict:
        """Get portfolio summary with current values."""
        positions = self.get_all_positions()
        
        total_cost = 0
        total_current_value = 0
        position_details = []
        
        for pos in positions:
            symbol = pos['symbol']
            shares = pos['shares']
            avg_price = pos['avg_buy_price']
            
            cost_basis = shares * avg_price
            current_price = current_prices.get(symbol, avg_price)
            current_value = shares * current_price
            
            profit_loss = current_value - cost_basis
            profit_loss_pct = (profit_loss / cost_basis * 100) if cost_basis > 0 else 0
            
            total_cost += cost_basis
            total_current_value += current_value
            
            position_details.append({
                'symbol': symbol,
                'shares': shares,
                'avg_buy_price': avg_price,
                'current_price': current_price,
                'cost_basis': cost_basis,
                'current_value': current_value,
                'profit_loss': profit_loss,
                'profit_loss_pct': profit_loss_pct
            })
        
        total_profit_loss = total_current_value - total_cost
        total_profit_loss_pct = (total_profit_loss / total_cost * 100) if total_cost > 0 else 0
        
        return {
            'positions': position_details,
            'total_cost': total_cost,
            'total_current_value': total_current_value,
            'total_profit_loss': total_profit_loss,
            'total_profit_loss_pct': total_profit_loss_pct,
            'position_count': len(positions)
        }
    
    def get_performance_stats(self) -> Dict:
        """Get overall performance statistics."""
        cursor = self.conn.cursor()
        
        # Get closed signals performance
        cursor.execute("""
            SELECT 
                COUNT(*) as total_signals,
                AVG(profit_loss) as avg_return,
                SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as winning_trades,
                SUM(CASE WHEN profit_loss < 0 THEN 1 ELSE 0 END) as losing_trades,
                MAX(profit_loss) as best_trade,
                MIN(profit_loss) as worst_trade
            FROM signal_history
            WHERE status = 'CLOSED'
        """)
        
        row = cursor.fetchone()
        
        total_signals = row[0] or 0
        avg_return = row[1] or 0
        winning_trades = row[2] or 0
        losing_trades = row[3] or 0
        best_trade = row[4] or 0
        worst_trade = row[5] or 0
        
        win_rate = (winning_trades / total_signals * 100) if total_signals > 0 else 0
        
        return {
            'total_signals': total_signals,
            'avg_return': avg_return,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'best_trade': best_trade,
            'worst_trade': worst_trade
        }
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
