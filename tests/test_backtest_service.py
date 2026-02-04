"""Unit tests for the BacktestService."""

import pandas as pd
import pytest
from services.backtest_service import BacktestService


@pytest.fixture
def sample_indicator_data() -> pd.DataFrame:
    dates = pd.date_range("2025-01-01", periods=6, freq="D")
    df = pd.DataFrame({
        "Close": [100, 95, 90, 105, 102, 98],
        "RSI": [50, 28, 22, 75, 60, 45],
        "MA_Short": [100, 103, 104, 105, 104, 102],
        "MA_Long": [99, 100, 101, 100, 101, 101],
    }, index=dates)
    return df


@pytest.fixture
def sample_ohlc_data() -> pd.DataFrame:
    dates = pd.date_range("2025-01-01", periods=10, freq="D")
    df = pd.DataFrame({
        "Open": [100, 95, 92, 90, 96, 104, 100, 110, 108, 112],
        "High": [105, 97, 93, 96, 101, 106, 103, 113, 110, 115],
        "Low": [95, 94, 89, 88, 92, 100, 99, 109, 107, 111],
        "Close": [100, 95, 92, 94, 99, 102, 101, 111, 109, 114],
        "Volume": [1_000_000] * 10,
    }, index=dates)
    return df


def test_parse_backtest_trades_creates_trade_objects():
    service = BacktestService()
    trades_df = pd.DataFrame({
        "EntryTime": [pd.Timestamp("2025-01-02")],
        "ExitTime": [pd.Timestamp("2025-01-04")],
        "Size": [100],
        "EntryPrice": [95.0],
        "ExitPrice": [105.0],
        "PnL": [1000.0],
        "ReturnPct": [10.0],
        "Tag": ["RSI"],
    })

    trades = service._parse_backtest_trades(trades_df, symbol="TEST", sentiment_score=0.2)

    assert len(trades) == 1
    trade = trades[0]
    assert trade.symbol == "TEST"
    assert trade.entry_price == 95.0
    assert trade.profit_loss == 1000.0
    assert trade.sentiment_score == 0.2


def test_format_equity_curve_returns_balance_records():
    service = BacktestService()
    equity_df = pd.DataFrame({"Equity": [1000, 1200, 1100]}, index=pd.date_range("2025-01-01", periods=3, freq="D"))

    curve = service._format_equity_curve(equity_df)

    assert len(curve) == 3
    assert curve[0]["balance"] == 1000
    assert curve[-1]["balance"] == 1100


def test_calculate_metrics_returns_zero_for_no_trades():
    service = BacktestService()
    metrics = service._calculate_metrics([], 100.0, 110.0)

    assert metrics["total_trades"] == 0
    assert metrics["win_rate"] == 0.0
    assert metrics["profit_factor"] == 0.0


def test_rsi_ma_backtest_reports_insufficient_data():
    service = BacktestService()
    empty_df = pd.DataFrame({"Close": [], "RSI": [], "MA_Short": [], "MA_Long": []})

    result = service.rsi_ma_backtest(empty_df, symbol="TEST")
    assert result["status"] == "INSUFFICIENT_DATA"


def test_get_news_sentiment_without_api_key():
    service = BacktestService()
    service.news_api_key = ""

    sentiment = service.get_news_sentiment("TEST")
    assert sentiment["status"] == "NO_API_KEY"
    assert sentiment["sentiment_score"] == 0.0


def test_rsi_ma_backtest_returns_trades_when_data_enough(sample_ohlc_data: pd.DataFrame):
    service = BacktestService()
    result = service.rsi_ma_backtest(
        sample_ohlc_data,
        symbol="TEST",
        rsi_period=5,
        ma_short=3,
        ma_long=5,
        use_sentiment=False
    )

    assert result["status"] == "SUCCESS"
    assert "metrics" in result
    assert isinstance(result["trades"], list)
    assert isinstance(result["equity_curve"], list)
