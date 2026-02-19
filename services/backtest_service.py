"""Backtesting service for all trading strategies with news sentiment."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
import requests
from backtesting import Backtest
from services.strategies import get_strategy, ALL_STRATEGIES, DAY_TRADING_STRATEGIES, SWING_TRADING_STRATEGIES
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


# Minimum bars each strategy needs before it can produce signals
STRATEGY_MIN_BARS: Dict[str, int] = {
    'vwap': 20,
    'orb': 10,
    'momentum': 30,
    'mean_reversion': 30,
    'fibonacci': 55,   # lookback_period (50) + warmup
    'breakout': 25,
}

# Strategies that require intraday (sub-daily) OHLCV data
DAY_TRADING_STRATEGY_NAMES = set(DAY_TRADING_STRATEGIES.keys())
SWING_TRADING_STRATEGY_NAMES = set(SWING_TRADING_STRATEGIES.keys())


class BacktestService:
    """Service for backtesting all trading strategies (day trading & swing)."""

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
    
    def run_backtest(
        self,
        ohlc_data: pd.DataFrame,
        symbol: str,
        strategy_name: str = 'mean_reversion',
        cash: float = 10_000.0,
        use_sentiment: bool = True,
        strategy_params: Optional[Dict] = None,
    ) -> Dict:
        """
        Run a backtest for any registered strategy.

        Args:
            ohlc_data: DataFrame with Open/High/Low/Close/Volume columns.
            symbol: Stock ticker (used for sentiment lookup).
            strategy_name: One of the keys in ALL_STRATEGIES
                           ('vwap', 'orb', 'momentum',
                            'mean_reversion', 'fibonacci', 'breakout').
            cash: Starting capital in dollars.
            use_sentiment: Fetch and attach news sentiment to results.
            strategy_params: Optional dict of strategy class-level parameter
                             overrides forwarded to ``Backtest.run()``.

        Returns:
            Dict with keys: status, strategy, trades, equity_curve, metrics,
                            sentiment, parameters.
        """
        strategy_name = strategy_name.lower()
        strategy_cls = get_strategy(strategy_name)

        if strategy_cls is None:
            available = ', '.join(sorted(ALL_STRATEGIES.keys()))
            return {
                'status': 'UNKNOWN_STRATEGY',
                'error': f"Strategy '{strategy_name}' not found. Available: {available}",
                'trades': [],
                'equity_curve': [],
                'metrics': {},
            }

        min_bars = STRATEGY_MIN_BARS.get(strategy_name, 30)
        if ohlc_data.empty or len(ohlc_data) < min_bars:
            return {
                'status': 'INSUFFICIENT_DATA',
                'error': f"Strategy '{strategy_name}' needs at least {min_bars} bars, "
                         f"got {len(ohlc_data)}.",
                'trades': [],
                'equity_curve': [],
                'metrics': {},
            }

        required_cols = {'Open', 'High', 'Low', 'Close', 'Volume'}
        missing = required_cols - set(ohlc_data.columns)
        if missing:
            return {
                'status': 'MISSING_COLUMNS',
                'error': f"DataFrame is missing columns: {missing}",
                'trades': [],
                'equity_curve': [],
                'metrics': {},
            }

        # Fetch sentiment (fire-and-forget; never blocks the backtest)
        sentiment = None
        sentiment_score = 0.0
        if use_sentiment:
            sentiment = self.get_news_sentiment(symbol)
            sentiment_score = sentiment.get('sentiment_score', 0.0)

        df = ohlc_data.copy()

        backtest = Backtest(df, strategy_cls, cash=cash, exclusive_orders=True)

        run_kwargs = strategy_params.copy() if strategy_params else {}

        try:
            result = backtest.run(**run_kwargs)
        except Exception as exc:
            return {
                'status': 'ERROR',
                'error': str(exc),
                'trades': [],
                'equity_curve': [],
                'metrics': {},
            }

        trades = self._parse_backtest_trades(result._trades, symbol, sentiment_score)
        metrics = self._extract_metrics(result, trades)
        equity_curve = self._format_equity_curve(result._equity_curve)

        return {
            'status': 'SUCCESS',
            'strategy': strategy_name,
            'strategy_type': 'day_trading' if strategy_name in DAY_TRADING_STRATEGY_NAMES else 'swing_trading',
            'symbol': symbol,
            'trades': trades,
            'equity_curve': equity_curve,
            'metrics': metrics,
            'sentiment': sentiment,
            'parameters': {
                'strategy_name': strategy_name,
                'cash': cash,
                'use_sentiment': use_sentiment,
                'sentiment_score': sentiment_score,
                **(run_kwargs or {}),
            },
        }

    def compare_strategies(
        self,
        ohlc_data: pd.DataFrame,
        symbol: str,
        strategy_names: Optional[List[str]] = None,
        cash: float = 10_000.0,
        use_sentiment: bool = False,
    ) -> Dict:
        """
        Run multiple strategies on the same data and return a ranked comparison.

        Args:
            ohlc_data: DataFrame with OHLCV columns.
            symbol: Stock ticker.
            strategy_names: List of strategy keys to run.  Defaults to all
                            strategies that are appropriate for the data length.
            cash: Starting capital per run.
            use_sentiment: Whether to attach sentiment data (fetched once and
                           reused across all runs to avoid redundant API calls).

        Returns:
            Dict with 'results' (list, ranked by net_profit desc) and 'summary'.
        """
        if strategy_names is None:
            strategy_names = list(ALL_STRATEGIES.keys())

        # Fetch sentiment once for all strategies
        sentiment = None
        sentiment_score = 0.0
        if use_sentiment:
            sentiment = self.get_news_sentiment(symbol)
            sentiment_score = sentiment.get('sentiment_score', 0.0)

        results = []
        for name in strategy_names:
            result = self.run_backtest(
                ohlc_data=ohlc_data,
                symbol=symbol,
                strategy_name=name,
                cash=cash,
                use_sentiment=False,   # Already fetched above
            )
            # Attach the shared sentiment
            result['sentiment'] = sentiment
            if result['metrics']:
                result['metrics']['sentiment_score'] = sentiment_score
            results.append(result)

        # Rank by net profit (successful runs first)
        successful = [r for r in results if r['status'] == 'SUCCESS']
        failed = [r for r in results if r['status'] != 'SUCCESS']
        successful.sort(key=lambda r: r['metrics'].get('net_profit', 0), reverse=True)

        summary = {
            'symbol': symbol,
            'total_strategies': len(strategy_names),
            'successful_runs': len(successful),
            'failed_runs': len(failed),
            'best_strategy': successful[0]['strategy'] if successful else None,
            'best_net_profit': successful[0]['metrics'].get('net_profit', 0) if successful else 0,
            'ranking': [
                {
                    'rank': i + 1,
                    'strategy': r['strategy'],
                    'strategy_type': r.get('strategy_type'),
                    'net_profit': r['metrics'].get('net_profit', 0),
                    'win_rate': r['metrics'].get('win_rate', 0),
                    'total_trades': r['metrics'].get('total_trades', 0),
                    'sharpe_ratio': r['metrics'].get('sharpe_ratio', 0),
                    'max_drawdown': r['metrics'].get('max_drawdown', 0),
                }
                for i, r in enumerate(successful)
            ],
        }

        return {
            'status': 'SUCCESS',
            'summary': summary,
            'results': successful + failed,
        }

    # ------------------------------------------------------------------
    # Legacy shim – keeps existing callers working without changes
    # ------------------------------------------------------------------

    def rsi_ma_backtest(
        self,
        ohlc_data: pd.DataFrame,
        symbol: str,
        rsi_period: int = 14,
        rsi_oversold: int = 30,
        rsi_overbought: int = 70,
        ma_short: int = 20,
        ma_long: int = 50,
        use_sentiment: bool = True,
        sentiment_threshold: float = -0.3,
        strategy_name: str = 'mean_reversion',
    ) -> Dict:
        """
        Backtest with optional RSI/MA parameter overrides.

        Delegates to ``run_backtest`` with the named strategy.  Pass
        ``strategy_name`` to select any registered strategy; defaults to
        'mean_reversion' (previously hard-coded behaviour).
        """
        # Only forward RSI params when the target strategy class declares them
        strategy_cls = get_strategy(strategy_name)
        declared = set(vars(strategy_cls).keys()) if strategy_cls else set()
        strategy_params = {
            k: v for k, v in {
                'rsi_oversold': rsi_oversold,
                'rsi_overbought': rsi_overbought,
            }.items()
            if k in declared
        }
        result = self.run_backtest(
            ohlc_data=ohlc_data,
            symbol=symbol,
            strategy_name=strategy_name,
            use_sentiment=use_sentiment,
            strategy_params=strategy_params,
        )
        # Augment parameters block for backward-compatibility
        if result.get('parameters') is not None:
            result['parameters'].update({
                'rsi_period': rsi_period,
                'rsi_oversold': rsi_oversold,
                'rsi_overbought': rsi_overbought,
                'ma_short': ma_short,
                'ma_long': ma_long,
                'sentiment_threshold': sentiment_threshold,
            })
        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

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
        return self._extract_metrics(None, trades)

    def _extract_metrics(self, result, trades: List[Trade]) -> Dict:
        """
        Build a metrics dict from the backtesting.py ``result`` Series and the
        parsed ``trades`` list.  Rich stats (Sharpe, drawdown, etc.) come from
        ``result`` when available; trade-level stats are always recalculated
        from ``trades`` for consistency.
        """
        winning_trades = [t for t in trades if t.profit_loss > 0]
        losing_trades = [t for t in trades if t.profit_loss < 0]

        total_profit = sum(t.profit_loss for t in winning_trades)
        total_loss = sum(t.profit_loss for t in losing_trades)

        win_rate = (len(winning_trades) / len(trades) * 100) if trades else 0.0
        avg_return = float(np.mean([t.return_pct for t in trades])) if trades else 0.0
        profit_factor = total_profit / abs(total_loss) if total_loss != 0 else 0.0
        avg_win = float(np.mean([t.profit_loss for t in winning_trades])) if winning_trades else 0.0
        avg_loss = float(np.mean([t.profit_loss for t in losing_trades])) if losing_trades else 0.0

        metrics = {
            'total_trades': len(trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': round(win_rate, 2),
            'avg_return': round(avg_return, 4),
            'best_trade': round(max((t.return_pct for t in trades), default=0.0), 4),
            'worst_trade': round(min((t.return_pct for t in trades), default=0.0), 4),
            'gross_profit': round(total_profit, 2),
            'gross_loss': round(total_loss, 2),
            'net_profit': round(total_profit + total_loss, 2),
            'profit_factor': round(profit_factor, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            # Rich stats – populated from backtesting.py when result is available
            'sharpe_ratio': None,
            'sortino_ratio': None,
            'calmar_ratio': None,
            'max_drawdown': None,
            'max_drawdown_pct': None,
            'exposure_pct': None,
            'return_pct': None,
            'buy_and_hold_return_pct': None,
        }

        if result is not None:
            def _get(key, default=None):
                try:
                    val = result[key]
                    return float(val) if val == val else default  # guard NaN
                except (KeyError, TypeError):
                    return default

            metrics.update({
                'sharpe_ratio': _get('Sharpe Ratio'),
                'sortino_ratio': _get('Sortino Ratio'),
                'calmar_ratio': _get('Calmar Ratio'),
                'max_drawdown': _get('Max. Drawdown [%]'),
                'max_drawdown_pct': _get('Max. Drawdown [%]'),
                'exposure_pct': _get('Exposure Time [%]'),
                'return_pct': _get('Return [%]'),
                'buy_and_hold_return_pct': _get('Buy & Hold Return [%]'),
            })

        return metrics
    
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
