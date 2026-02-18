"""Backtesting service for swing trading strategies with news sentiment."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
import requests
from backtesting import Backtest
from services.strategies import get_strategy
from config.settings import settings


@dataclass
class Trade:
    """Represents a single executed trade from a backtest."""
    entry_date: str
    exit_date: str
    symbol: str
    shares: float
    entry_price: float
    exit_price: float
    profit_loss: float
    profit_loss_pct: float
    return_pct: float
    trade_type: str = "BUY"
    sentiment_score: float = 0.0
    notes: str = ""


class BacktestService:
    """Service for backtesting swing trading strategies."""
    
    def __init__(self):
        """Initialize backtest service."""
        self.news_api_key = settings.NEWS_API_KEY
        self.trades = []
        self.equity_curve = []
    
    def get_news_sentiment(self, symbol: str, days: int = 7) -> Dict[str, any]:
        """
        Get news sentiment for a symbol using NewsAPI.
        
        Args:
            symbol: Stock ticker
            days: Number of days to look back
        
        Returns:
            Dict with sentiment score, count, and articles
        """
        if not self.news_api_key:
            return {
                'sentiment_score': 0.0,
                'article_count': 0,
                'articles': [],
                'status': 'NO_API_KEY'
            }
        
        try:
            # Calculate date range
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            
            # Query NewsAPI
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': symbol,
                'from': start_date,
                'to': end_date,
                'sortBy': 'publishedAt',
                'language': 'en',
                'pageSize': 50,
                'apiKey': self.news_api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            articles = data.get('articles', [])
            
            if not articles:
                return {
                    'sentiment_score': 0.0,
                    'article_count': 0,
                    'articles': [],
                    'status': 'NO_NEWS'
                }
            
            # Simple sentiment scoring from headlines
            sentiment_scores = []
            for article in articles:
                headline = article.get('title', '').lower()
                description = article.get('description', '').lower() if article.get('description') else ''
                combined = headline + ' ' + description
                
                # Simple keyword-based sentiment
                positive_words = ['surge', 'gain', 'profit', 'bull', 'up', 'rally', 'strong', 'beat', 'upbeat', 'growth']
                negative_words = ['drop', 'loss', 'bear', 'down', 'fall', 'decline', 'weak', 'miss', 'downbeat', 'crash']
                
                pos_count = sum(1 for word in positive_words if word in combined)
                neg_count = sum(1 for word in negative_words if word in combined)
                
                if pos_count > neg_count:
                    sentiment_scores.append(0.5)
                elif neg_count > pos_count:
                    sentiment_scores.append(-0.5)
                else:
                    sentiment_scores.append(0.0)
            
            avg_sentiment = np.mean(sentiment_scores) if sentiment_scores else 0.0
            
            return {
                'sentiment_score': round(avg_sentiment, 2),
                'article_count': len(articles),
                'articles': articles[:10],  # Top 10 articles
                'status': 'SUCCESS'
            }
        
        except requests.exceptions.RequestException as e:
            return {
                'sentiment_score': 0.0,
                'article_count': 0,
                'articles': [],
                'status': f'ERROR: {str(e)}'
            }
    
    def rsi_ma_backtest(self, ohlc_data: pd.DataFrame, symbol: str,
                       rsi_period: int = 14, rsi_oversold: int = 30, rsi_overbought: int = 70,
                       ma_short: int = 20, ma_long: int = 50,
                       use_sentiment: bool = True, sentiment_threshold: float = -0.3) -> Dict:
        """
        Backtest RSI + Moving Average crossover strategy with optional sentiment filter.
        
        Args:
            ohlc_data: DataFrame with OHLC data
            symbol: Stock ticker
            rsi_period: RSI period
            rsi_oversold: RSI oversold threshold
            rsi_overbought: RSI overbought threshold
            ma_short: Short MA period
            ma_long: Long MA period
            use_sentiment: Whether to filter by news sentiment
            sentiment_threshold: Minimum sentiment for BUY signals
        
        Returns:
            Dict with backtest results
        """
        if ohlc_data.empty or len(ohlc_data) < max(rsi_period, ma_long):
            return {
                'status': 'INSUFFICIENT_DATA',
                'trades': [],
                'equity_curve': [],
                'metrics': {}
            }
        
        df = ohlc_data.copy()
        
        # Calculate indicators
        df = self._calculate_indicators(df, rsi_period, ma_short, ma_long)

        # Get sentiment (if enabled)
        sentiment = None
        sentiment_score = 0.0
        if use_sentiment:
            sentiment = self.get_news_sentiment(symbol)
            sentiment_score = sentiment.get('sentiment_score', 0.0)

        market_df = df.copy()

        if market_df.empty or len(market_df) < max(rsi_period, ma_long):
            return {
                'status': 'INSUFFICIENT_DATA',
                'trades': [],
                'equity_curve': [],
                'metrics': {}
            }

        # Select strategy class based on symbol hint or default to swing
        strategy_cls = get_strategy('vwap') if "day" in symbol.lower() else get_strategy('mean_reversion')
        if strategy_cls is None:
            strategy_cls = get_strategy('mean_reversion')
        
        backtest = Backtest(market_df, strategy_cls, cash=10000, exclusive_orders=True)

        try:
            # Pass news parameters to the strategy
            result = backtest.run(
                sentiment_score=sentiment_score,
                news_relevance=sentiment.get('relevance', 50) if sentiment else 50
            )
        except Exception as exc:
            return {
                'status': 'ERROR',
                'error': str(exc),
                'trades': [],
                'equity_curve': [],
                'metrics': {}
            }

        trades = self._parse_backtest_trades(result._trades, symbol, sentiment_score)

        metrics = self._calculate_metrics(
            trades,
            market_df['Close'].iloc[0],
            market_df['Close'].iloc[-1]
        )

        equity_curve = self._format_equity_curve(result._equity_curve)

        return {
            'status': 'SUCCESS',
            'trades': trades,
            'equity_curve': equity_curve,
            'metrics': metrics,
            'sentiment': sentiment,
            'parameters': {
                'rsi_period': rsi_period,
                'rsi_oversold': rsi_oversold,
                'rsi_overbought': rsi_overbought,
                'ma_short': ma_short,
                'ma_long': ma_long,
                'use_sentiment': use_sentiment,
                'sentiment_threshold': sentiment_threshold,
                'sentiment_score': sentiment_score
            }
        }
    
    def _calculate_indicators(self, df: pd.DataFrame, rsi_period: int,
                             ma_short: int, ma_long: int) -> pd.DataFrame:
        """Calculate technical indicators."""
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Moving Averages
        df['MA_Short'] = df['Close'].rolling(window=ma_short).mean()
        df['MA_Long'] = df['Close'].rolling(window=ma_long).mean()
        
        return df
    
    def _parse_backtest_trades(self, trades_df: pd.DataFrame, symbol: str, sentiment_score: float) -> List[Trade]:
        """Convert backtesting.py trades to Trade dataclasses."""
        trades = []
        for _, row in trades_df.iterrows():
            entry_time = row.EntryTime
            exit_time = row.ExitTime
            entry_date = entry_time.strftime("%Y-%m-%d") if hasattr(entry_time, 'strftime') else str(entry_time)
            exit_date = exit_time.strftime("%Y-%m-%d") if hasattr(exit_time, 'strftime') else str(exit_time)

            trades.append(Trade(
                entry_date=entry_date,
                exit_date=exit_date,
                symbol=symbol,
                shares=float(row.Size),
                entry_price=float(row.EntryPrice),
                exit_price=float(row.ExitPrice),
                profit_loss=float(row.PnL),
                profit_loss_pct=float(row.ReturnPct),
                return_pct=float(row.ReturnPct),
                trade_type='BUY',
                sentiment_score=sentiment_score,
                notes=getattr(row, 'Tag', '') or ''
            ))
        return trades
    
    def _calculate_metrics(self, trades: List[Trade], start_price: float,
                          end_price: float) -> Dict:
        """Calculate backtest performance metrics."""
        if not trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'avg_return': 0.0,
                'best_trade': 0.0,
                'worst_trade': 0.0,
                'gross_profit': 0.0,
                'gross_loss': 0.0,
                'net_profit': 0.0,
                'profit_factor': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0
            }
        
        winning_trades = [t for t in trades if t.profit_loss > 0]
        losing_trades = [t for t in trades if t.profit_loss < 0]
        
        total_profit = sum(t.profit_loss for t in winning_trades)
        total_loss = sum(t.profit_loss for t in losing_trades)
        
        win_rate = (len(winning_trades) / len(trades) * 100) if trades else 0
        avg_return = np.mean([t.return_pct for t in trades]) if trades else 0
        
        profit_factor = total_profit / abs(total_loss) if total_loss != 0 else 0
        avg_win = np.mean([t.profit_loss for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.profit_loss for t in losing_trades]) if losing_trades else 0
        
        return {
            'total_trades': len(trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': round(win_rate, 2),
            'avg_return': round(avg_return, 2),
            'best_trade': max([t.return_pct for t in trades]) if trades else 0,
            'worst_trade': min([t.return_pct for t in trades]) if trades else 0,
            'gross_profit': round(total_profit, 2),
            'gross_loss': round(total_loss, 2),
            'net_profit': round(total_profit + total_loss, 2),
            'profit_factor': round(profit_factor, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2)
        }
    
    def _format_equity_curve(self, equity_df: pd.DataFrame) -> List[Dict]:
        if equity_df is None or equity_df.empty:
            return []

        curve = []
        for idx, row in equity_df.iterrows():
            date = idx.strftime("%Y-%m-%d") if hasattr(idx, 'strftime') else str(idx)
            curve.append({
                'date': date,
                'balance': float(row.Equity)
            })
        return curve
