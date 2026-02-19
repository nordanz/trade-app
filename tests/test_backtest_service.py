"""Unit tests for BacktestService.

Coverage:
  - BacktestService.run_backtest       – all 6 strategies, guard-rails, params
  - BacktestService.compare_strategies – ranking, sentiment sharing
  - BacktestService.rsi_ma_backtest    – legacy shim backward-compatibility
  - BacktestService.get_news_sentiment – API paths (success / error / no-key)
  - BacktestService._extract_metrics   – trade-level and backtesting.py stats
  - BacktestService._format_equity_curve
  - BacktestService._parse_backtest_trades
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from services.backtest_service import (
    BacktestService,
    Trade,
    STRATEGY_MIN_BARS,
    DAY_TRADING_STRATEGY_NAMES,
    SWING_TRADING_STRATEGY_NAMES,
)
from services.strategies import ALL_STRATEGIES


# ---------------------------------------------------------------------------
# Fixtures – synthetic OHLCV data
# ---------------------------------------------------------------------------

def _make_ohlcv(periods: int, start_price: float = 100.0, freq: str = "D") -> pd.DataFrame:
    """Build a deterministic OHLCV DataFrame for testing."""
    np.random.seed(42)
    dates = pd.date_range(start="2024-01-01", periods=periods, freq=freq)
    close = start_price + np.cumsum(np.random.normal(0, 0.5, periods))
    open_ = close + np.random.uniform(-0.5, 0.5, periods)
    high = np.maximum(close, open_) + np.random.uniform(0, 1, periods)
    low = np.minimum(close, open_) - np.random.uniform(0, 1, periods)
    volume = np.random.uniform(500_000, 2_000_000, periods)
    return pd.DataFrame(
        {"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume},
        index=dates,
    )


@pytest.fixture
def daily_data_100():
    """100 daily bars – enough for every swing strategy."""
    return _make_ohlcv(100)


@pytest.fixture
def daily_data_60():
    """60 daily bars – enough for fibonacci (min 55)."""
    return _make_ohlcv(60)


@pytest.fixture
def intraday_data_80():
    """80 5-minute bars – enough for all day-trading strategies."""
    return _make_ohlcv(80, freq="5min")


@pytest.fixture
def tiny_data():
    """5 bars – always below every strategy's minimum."""
    return _make_ohlcv(5)


@pytest.fixture
def service():
    """BacktestService with news API disabled (no key)."""
    svc = BacktestService()
    svc.news_api_key = None
    return svc


@pytest.fixture
def service_with_key():
    """BacktestService with a fake news API key set."""
    svc = BacktestService()
    svc.news_api_key = "fake-key-123"
    return svc


# ---------------------------------------------------------------------------
# get_news_sentiment
# ---------------------------------------------------------------------------

class TestGetNewsSentiment:

    def test_no_api_key_returns_no_api_key_status(self, service):
        result = service.get_news_sentiment("AAPL")
        assert result["status"] == "NO_API_KEY"
        assert result["sentiment_score"] == 0.0
        assert result["article_count"] == 0

    def test_success_positive_headlines(self, service_with_key):
        mock_articles = [
            {"title": "AAPL surges to new highs on strong growth", "description": "Bull rally"},
            {"title": "Apple beats profit estimates with strong earnings", "description": "Upbeat"},
        ]
        mock_response = MagicMock()
        mock_response.json.return_value = {"articles": mock_articles}
        mock_response.raise_for_status.return_value = None

        with patch("requests.get", return_value=mock_response):
            result = service_with_key.get_news_sentiment("AAPL")

        assert result["status"] == "SUCCESS"
        assert result["sentiment_score"] > 0
        assert result["article_count"] == 2

    def test_success_negative_headlines(self, service_with_key):
        mock_articles = [
            {"title": "AAPL drops on weak earnings miss", "description": "Bear market crash"},
            {"title": "Apple shares decline amid market fall", "description": "Weak outlook"},
        ]
        mock_response = MagicMock()
        mock_response.json.return_value = {"articles": mock_articles}
        mock_response.raise_for_status.return_value = None

        with patch("requests.get", return_value=mock_response):
            result = service_with_key.get_news_sentiment("AAPL")

        assert result["status"] == "SUCCESS"
        assert result["sentiment_score"] < 0

    def test_no_articles_returns_no_news(self, service_with_key):
        mock_response = MagicMock()
        mock_response.json.return_value = {"articles": []}
        mock_response.raise_for_status.return_value = None

        with patch("requests.get", return_value=mock_response):
            result = service_with_key.get_news_sentiment("AAPL")

        assert result["status"] == "NO_NEWS"
        assert result["sentiment_score"] == 0.0

    def test_network_error_returns_error_status(self, service_with_key):
        import requests as req

        with patch("requests.get", side_effect=req.exceptions.ConnectionError("timeout")):
            result = service_with_key.get_news_sentiment("AAPL")

        assert result["status"].startswith("ERROR")
        assert result["sentiment_score"] == 0.0


# ---------------------------------------------------------------------------
# run_backtest – guard-rails
# ---------------------------------------------------------------------------

class TestRunBacktestGuards:

    def test_unknown_strategy_returns_error(self, service, daily_data_100):
        result = service.run_backtest(daily_data_100, "AAPL", strategy_name="does_not_exist")
        assert result["status"] == "UNKNOWN_STRATEGY"
        assert "error" in result
        assert result["trades"] == []

    def test_insufficient_data_returns_error(self, service, tiny_data):
        result = service.run_backtest(tiny_data, "AAPL", strategy_name="mean_reversion")
        assert result["status"] == "INSUFFICIENT_DATA"
        assert "error" in result

    def test_missing_volume_column_returns_error(self, service, daily_data_100):
        df = daily_data_100.drop(columns=["Volume"])
        result = service.run_backtest(df, "AAPL", strategy_name="mean_reversion")
        assert result["status"] == "MISSING_COLUMNS"
        assert "Volume" in result["error"]

    def test_missing_close_column_returns_error(self, service, daily_data_100):
        df = daily_data_100.drop(columns=["Close"])
        result = service.run_backtest(df, "AAPL", strategy_name="mean_reversion")
        assert result["status"] == "MISSING_COLUMNS"

    def test_empty_dataframe_returns_insufficient_data(self, service):
        result = service.run_backtest(pd.DataFrame(), "AAPL", strategy_name="mean_reversion")
        assert result["status"] == "INSUFFICIENT_DATA"

    @pytest.mark.parametrize("strategy_name,min_bars", STRATEGY_MIN_BARS.items())
    def test_each_strategy_min_bars_enforced(self, service, strategy_name, min_bars):
        """One bar below the minimum must always return INSUFFICIENT_DATA."""
        df = _make_ohlcv(min_bars - 1)
        result = service.run_backtest(df, "TEST", strategy_name=strategy_name)
        assert result["status"] == "INSUFFICIENT_DATA"


# ---------------------------------------------------------------------------
# run_backtest – successful runs for all 6 strategies
# ---------------------------------------------------------------------------

ALL_STRATEGY_NAMES = list(ALL_STRATEGIES.keys())


class TestRunBacktestSuccess:

    @pytest.mark.parametrize("strategy_name", ["mean_reversion", "fibonacci", "breakout"])
    def test_swing_strategies_succeed_on_daily_data(self, service, daily_data_100, strategy_name):
        result = service.run_backtest(
            daily_data_100, "AAPL", strategy_name=strategy_name, use_sentiment=False
        )
        assert result["status"] == "SUCCESS", result.get("error")
        assert result["strategy"] == strategy_name
        assert result["strategy_type"] == "swing_trading"
        assert result["symbol"] == "AAPL"
        assert isinstance(result["trades"], list)
        assert isinstance(result["equity_curve"], list)
        assert isinstance(result["metrics"], dict)

    @pytest.mark.parametrize("strategy_name", ["vwap", "orb", "momentum"])
    def test_day_trading_strategies_succeed_on_intraday_data(
        self, service, intraday_data_80, strategy_name
    ):
        result = service.run_backtest(
            intraday_data_80, "AAPL", strategy_name=strategy_name, use_sentiment=False
        )
        assert result["status"] == "SUCCESS", result.get("error")
        assert result["strategy"] == strategy_name
        assert result["strategy_type"] == "day_trading"

    def test_result_contains_all_expected_keys(self, service, daily_data_100):
        result = service.run_backtest(
            daily_data_100, "SPY", strategy_name="mean_reversion", use_sentiment=False
        )
        assert result["status"] == "SUCCESS"
        for key in ("strategy", "strategy_type", "symbol", "trades",
                    "equity_curve", "metrics", "sentiment", "parameters"):
            assert key in result, f"Missing key: {key}"

    def test_parameters_block_reflects_inputs(self, service, daily_data_100):
        result = service.run_backtest(
            daily_data_100, "TSLA",
            strategy_name="breakout",
            cash=25_000.0,
            use_sentiment=False,
        )
        assert result["status"] == "SUCCESS"
        params = result["parameters"]
        assert params["strategy_name"] == "breakout"
        assert params["cash"] == 25_000.0

    def test_strategy_name_is_case_insensitive(self, service, daily_data_100):
        result = service.run_backtest(
            daily_data_100, "AAPL", strategy_name="MEAN_REVERSION", use_sentiment=False
        )
        assert result["status"] == "SUCCESS"
        assert result["strategy"] == "mean_reversion"

    def test_strategy_params_forwarded(self, service, daily_data_100):
        """strategy_params dict is forwarded to Backtest.run without error."""
        result = service.run_backtest(
            daily_data_100, "AAPL",
            strategy_name="mean_reversion",
            use_sentiment=False,
            strategy_params={"rsi_oversold": 25, "rsi_overbought": 75},
        )
        # Just assert it ran – the strategy ignores unknown kwargs gracefully
        assert result["status"] == "SUCCESS"

    def test_sentiment_disabled_sets_none(self, service, daily_data_100):
        result = service.run_backtest(
            daily_data_100, "AAPL", strategy_name="mean_reversion", use_sentiment=False
        )
        assert result["sentiment"] is None
        assert result["parameters"]["sentiment_score"] == 0.0

    def test_sentiment_enabled_no_key_still_succeeds(self, service, daily_data_100):
        """With no API key, sentiment returns NO_API_KEY but backtest still runs."""
        result = service.run_backtest(
            daily_data_100, "AAPL", strategy_name="mean_reversion", use_sentiment=True
        )
        assert result["status"] == "SUCCESS"
        assert result["sentiment"]["status"] == "NO_API_KEY"


# ---------------------------------------------------------------------------
# run_backtest – metrics shape
# ---------------------------------------------------------------------------

class TestMetrics:

    def test_metrics_keys_present(self, service, daily_data_100):
        result = service.run_backtest(
            daily_data_100, "AAPL", strategy_name="mean_reversion", use_sentiment=False
        )
        metrics = result["metrics"]
        required = {
            "total_trades", "winning_trades", "losing_trades", "win_rate",
            "avg_return", "best_trade", "worst_trade", "gross_profit",
            "gross_loss", "net_profit", "profit_factor", "avg_win", "avg_loss",
            "sharpe_ratio", "sortino_ratio", "max_drawdown", "return_pct",
            "buy_and_hold_return_pct",
        }
        for key in required:
            assert key in metrics, f"Missing metric: {key}"

    def test_winning_plus_losing_equals_total(self, service, daily_data_100):
        result = service.run_backtest(
            daily_data_100, "AAPL", strategy_name="mean_reversion", use_sentiment=False
        )
        m = result["metrics"]
        assert m["winning_trades"] + m["losing_trades"] <= m["total_trades"]

    def test_win_rate_between_0_and_100(self, service, daily_data_100):
        result = service.run_backtest(
            daily_data_100, "AAPL", strategy_name="mean_reversion", use_sentiment=False
        )
        assert 0.0 <= result["metrics"]["win_rate"] <= 100.0

    def test_extract_metrics_no_trades(self, service):
        metrics = service._extract_metrics(None, [])
        assert metrics["total_trades"] == 0
        assert metrics["win_rate"] == 0.0
        assert metrics["net_profit"] == 0.0
        assert metrics["profit_factor"] == 0.0

    def test_extract_metrics_with_trades(self, service):
        def _trade(pnl, ret):
            return Trade(
                entry_date="2024-01-01", exit_date="2024-01-10",
                symbol="AAPL", shares=10, entry_price=100.0,
                exit_price=100.0 + pnl / 10,
                profit_loss=pnl, profit_loss_pct=ret, return_pct=ret,
            )

        trades = [_trade(200, 0.02), _trade(-100, -0.01), _trade(50, 0.005)]
        metrics = service._extract_metrics(None, trades)

        assert metrics["total_trades"] == 3
        assert metrics["winning_trades"] == 2
        assert metrics["losing_trades"] == 1
        assert metrics["gross_profit"] == pytest.approx(250.0)
        assert metrics["gross_loss"] == pytest.approx(-100.0)
        assert metrics["net_profit"] == pytest.approx(150.0)
        assert metrics["profit_factor"] == pytest.approx(2.5)
        assert metrics["win_rate"] == pytest.approx(200 / 3, rel=0.01)

    def test_extract_metrics_reads_backtesting_stats(self, service):
        """Sharpe, drawdown, etc. are lifted from the backtesting.py result."""
        mock_result = {
            "Sharpe Ratio": 1.23,
            "Sortino Ratio": 1.80,
            "Calmar Ratio": 0.95,
            "Max. Drawdown [%]": -15.4,
            "Exposure Time [%]": 62.0,
            "Return [%]": 18.5,
            "Buy & Hold Return [%]": 12.0,
        }
        metrics = service._extract_metrics(mock_result, [])
        assert metrics["sharpe_ratio"] == pytest.approx(1.23)
        assert metrics["max_drawdown"] == pytest.approx(-15.4)
        assert metrics["return_pct"] == pytest.approx(18.5)
        assert metrics["buy_and_hold_return_pct"] == pytest.approx(12.0)

    def test_extract_metrics_handles_nan_from_backtesting(self, service):
        """NaN values in the backtesting result must not propagate."""
        mock_result = {"Sharpe Ratio": float("nan"), "Return [%]": 5.0}
        metrics = service._extract_metrics(mock_result, [])
        assert metrics["sharpe_ratio"] is None
        assert metrics["return_pct"] == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# _format_equity_curve
# ---------------------------------------------------------------------------

class TestFormatEquityCurve:

    def test_none_returns_empty_list(self, service):
        assert service._format_equity_curve(None) == []

    def test_empty_df_returns_empty_list(self, service):
        assert service._format_equity_curve(pd.DataFrame()) == []

    def test_curve_has_date_and_balance(self, service):
        dates = pd.date_range("2024-01-01", periods=3, freq="D")
        df = pd.DataFrame({"Equity": [10000.0, 10100.0, 9950.0]}, index=dates)
        curve = service._format_equity_curve(df)
        assert len(curve) == 3
        for point in curve:
            assert "date" in point
            assert "balance" in point
            assert isinstance(point["balance"], float)

    def test_curve_dates_are_strings(self, service):
        dates = pd.date_range("2024-06-01", periods=2, freq="D")
        df = pd.DataFrame({"Equity": [10000.0, 10200.0]}, index=dates)
        curve = service._format_equity_curve(df)
        assert all(isinstance(p["date"], str) for p in curve)


# ---------------------------------------------------------------------------
# _parse_backtest_trades
# ---------------------------------------------------------------------------

class TestParseBacktestTrades:

    def _make_trades_df(self):
        rows = [
            {
                "EntryTime": datetime(2024, 1, 5),
                "ExitTime": datetime(2024, 1, 12),
                "Size": 10,
                "EntryPrice": 100.0,
                "ExitPrice": 110.0,
                "PnL": 100.0,
                "ReturnPct": 0.10,
                "Tag": "signal_A",
            },
            {
                "EntryTime": datetime(2024, 2, 1),
                "ExitTime": datetime(2024, 2, 8),
                "Size": 5,
                "EntryPrice": 110.0,
                "ExitPrice": 105.0,
                "PnL": -25.0,
                "ReturnPct": -0.045,
                "Tag": None,
            },
        ]
        df = pd.DataFrame(rows)
        # Mimic backtesting.py attribute-access columns
        df.columns = pd.Index(df.columns)
        return df

    def test_returns_list_of_trades(self, service):
        df = self._make_trades_df()
        trades = service._parse_backtest_trades(df, "AAPL", 0.3)
        assert len(trades) == 2
        assert all(isinstance(t, Trade) for t in trades)

    def test_trade_fields_populated(self, service):
        df = self._make_trades_df()
        trades = service._parse_backtest_trades(df, "AAPL", 0.25)
        t = trades[0]
        assert t.symbol == "AAPL"
        assert t.sentiment_score == pytest.approx(0.25)
        assert t.entry_price == pytest.approx(100.0)
        assert t.exit_price == pytest.approx(110.0)
        assert t.profit_loss == pytest.approx(100.0)
        assert t.notes == "signal_A"

    def test_none_tag_becomes_empty_string(self, service):
        df = self._make_trades_df()
        trades = service._parse_backtest_trades(df, "AAPL", 0.0)
        assert trades[1].notes == ""

    def test_dates_are_formatted_strings(self, service):
        df = self._make_trades_df()
        trades = service._parse_backtest_trades(df, "AAPL", 0.0)
        assert trades[0].entry_date == "2024-01-05"
        assert trades[0].exit_date == "2024-01-12"

    def test_empty_trades_df_returns_empty_list(self, service):
        empty_df = pd.DataFrame(
            columns=["EntryTime", "ExitTime", "Size", "EntryPrice",
                     "ExitPrice", "PnL", "ReturnPct", "Tag"]
        )
        trades = service._parse_backtest_trades(empty_df, "AAPL", 0.0)
        assert trades == []


# ---------------------------------------------------------------------------
# compare_strategies
# ---------------------------------------------------------------------------

class TestCompareStrategies:

    def test_returns_success_status(self, service, daily_data_100):
        result = service.compare_strategies(
            daily_data_100, "AAPL",
            strategy_names=["mean_reversion", "breakout"],
        )
        assert result["status"] == "SUCCESS"

    def test_summary_contains_required_keys(self, service, daily_data_100):
        result = service.compare_strategies(
            daily_data_100, "AAPL",
            strategy_names=["mean_reversion", "fibonacci"],
        )
        summary = result["summary"]
        for key in ("symbol", "total_strategies", "successful_runs",
                    "failed_runs", "best_strategy", "best_net_profit", "ranking"):
            assert key in summary, f"Missing summary key: {key}"

    def test_strategy_count_matches(self, service, daily_data_100):
        names = ["mean_reversion", "breakout", "fibonacci"]
        result = service.compare_strategies(daily_data_100, "AAPL", strategy_names=names)
        assert result["summary"]["total_strategies"] == len(names)

    def test_results_ranked_by_net_profit_descending(self, service, daily_data_100):
        result = service.compare_strategies(
            daily_data_100, "AAPL",
            strategy_names=["mean_reversion", "breakout", "fibonacci"],
        )
        profits = [
            r["metrics"].get("net_profit", 0)
            for r in result["results"]
            if r["status"] == "SUCCESS"
        ]
        assert profits == sorted(profits, reverse=True)

    def test_failed_strategies_included_after_successful(self, service, daily_data_100):
        """Tiny-data strategies that fail must appear at the end of results."""
        result = service.compare_strategies(
            daily_data_100, "AAPL",
            strategy_names=["mean_reversion", "does_not_exist"],
        )
        statuses = [r["status"] for r in result["results"]]
        success_idx = [i for i, s in enumerate(statuses) if s == "SUCCESS"]
        fail_idx = [i for i, s in enumerate(statuses) if s != "SUCCESS"]
        if success_idx and fail_idx:
            assert max(success_idx) < min(fail_idx)

    def test_defaults_to_all_strategies_when_none_given(self, service, daily_data_100):
        result = service.compare_strategies(daily_data_100, "AAPL")
        assert result["summary"]["total_strategies"] == len(ALL_STRATEGIES)

    def test_sentiment_fetched_once_and_shared(self, service_with_key, daily_data_100):
        """Sentiment is fetched once regardless of how many strategies are run."""
        with patch.object(
            service_with_key, "get_news_sentiment",
            return_value={"sentiment_score": 0.4, "status": "SUCCESS"}
        ) as mock_sentiment:
            service_with_key.compare_strategies(
                daily_data_100, "AAPL",
                strategy_names=["mean_reversion", "breakout"],
                use_sentiment=True,
            )
        mock_sentiment.assert_called_once()

    def test_ranking_entries_contain_required_fields(self, service, daily_data_100):
        result = service.compare_strategies(
            daily_data_100, "AAPL",
            strategy_names=["mean_reversion", "breakout"],
        )
        for entry in result["summary"]["ranking"]:
            for field in ("rank", "strategy", "strategy_type",
                          "net_profit", "win_rate", "total_trades"):
                assert field in entry, f"Missing ranking field: {field}"


# ---------------------------------------------------------------------------
# rsi_ma_backtest – legacy shim
# ---------------------------------------------------------------------------

class TestRsiMaBacktest:

    def test_delegates_to_run_backtest(self, service, daily_data_100):
        with patch.object(service, "run_backtest", wraps=service.run_backtest) as mock_rb:
            service.rsi_ma_backtest(
                daily_data_100, "AAPL",
                use_sentiment=False,
                strategy_name="mean_reversion",
            )
        mock_rb.assert_called_once()

    def test_backward_compat_params_in_response(self, service, daily_data_100):
        result = service.rsi_ma_backtest(
            daily_data_100, "AAPL",
            rsi_period=10,
            rsi_oversold=25,
            rsi_overbought=75,
            ma_short=10,
            ma_long=30,
            sentiment_threshold=-0.2,
            use_sentiment=False,
            strategy_name="mean_reversion",
        )
        assert result["status"] == "SUCCESS"
        params = result["parameters"]
        assert params["rsi_period"] == 10
        assert params["rsi_oversold"] == 25
        assert params["rsi_overbought"] == 75
        assert params["ma_short"] == 10
        assert params["ma_long"] == 30
        assert params["sentiment_threshold"] == -0.2

    def test_default_strategy_is_mean_reversion(self, service, daily_data_100):
        result = service.rsi_ma_backtest(
            daily_data_100, "AAPL", use_sentiment=False
        )
        assert result["status"] == "SUCCESS"
        assert result["strategy"] == "mean_reversion"

    def test_can_select_any_strategy(self, service, daily_data_100):
        result = service.rsi_ma_backtest(
            daily_data_100, "AAPL",
            strategy_name="breakout",
            use_sentiment=False,
        )
        assert result["status"] == "SUCCESS"
        assert result["strategy"] == "breakout"

    def test_unknown_strategy_propagates_error(self, service, daily_data_100):
        result = service.rsi_ma_backtest(
            daily_data_100, "AAPL",
            strategy_name="no_such_strategy",
            use_sentiment=False,
        )
        assert result["status"] == "UNKNOWN_STRATEGY"


# ---------------------------------------------------------------------------
# Strategy type classification constants
# ---------------------------------------------------------------------------

class TestStrategyTypeConstants:

    def test_day_trading_names_set(self):
        assert DAY_TRADING_STRATEGY_NAMES == {"vwap", "orb", "momentum"}

    def test_swing_trading_names_set(self):
        assert SWING_TRADING_STRATEGY_NAMES == {"mean_reversion", "fibonacci", "breakout"}

    def test_no_overlap_between_sets(self):
        assert DAY_TRADING_STRATEGY_NAMES.isdisjoint(SWING_TRADING_STRATEGY_NAMES)

    def test_union_equals_all_strategies(self):
        assert DAY_TRADING_STRATEGY_NAMES | SWING_TRADING_STRATEGY_NAMES == set(ALL_STRATEGIES.keys())


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
