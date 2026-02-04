"""Tests for PortfolioDB operations."""

import pytest
from services.portfolio_service import PortfolioDB


def _copy_db_path(tmp_path):
    return str(tmp_path / "test_portfolio.db")


@pytest.fixture
def portfolio_db(tmp_path):
    db_path = _copy_db_path(tmp_path)
    db = PortfolioDB(db_path)
    yield db
    db.conn.close()


def test_add_and_retrieve_position(portfolio_db):
    position_id = portfolio_db.add_position("TST", 10, 100.0, purchase_date="2025-02-01")
    assert position_id is not None

    position = portfolio_db.get_position("TST")
    assert position is not None
    assert position["symbol"] == "TST"
    assert position["shares"] == 10


def test_sell_removes_position_when_empty(portfolio_db):
    portfolio_db.add_position("TST", 5, 100.0)
    success = portfolio_db.sell_position("TST", 5, 110.0)
    assert success
    assert portfolio_db.get_position("TST") is None


def test_portfolio_summary_calculates_value(portfolio_db):
    portfolio_db.add_position("TST", 2, 50.0)
    summary = portfolio_db.get_portfolio_summary({"TST": 60.0})

    assert summary["position_count"] == 1
    assert summary["total_current_value"] == pytest.approx(120.0)
    assert summary["positions"][0]["profit_loss"] == pytest.approx(20.0)


def test_save_signal_and_fetch(portfolio_db):
    signal_id = portfolio_db.save_signal(
        symbol="TST",
        signal_type="BUY",
        confidence=70.0,
        entry_price=100,
        target_price=110,
        stop_loss=95,
        reasoning="Test signal"
    )

    signals = portfolio_db.get_signals(symbol="TST", limit=5)
    assert any(sig["id"] == signal_id for sig in signals)
