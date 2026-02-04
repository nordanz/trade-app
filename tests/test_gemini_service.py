"""Unit tests covering the Gemini AI service."""

from types import SimpleNamespace

import pytest

from models.trading_signal import Sentiment
from services.gemini_service import GeminiService


class _DummyModels:
    def __init__(self, response_text: str):
        self.response_text = response_text

    def generate_content(self, **kwargs) -> SimpleNamespace:
        return SimpleNamespace(text=self.response_text)


class _DummyClient:
    def __init__(self, response_text: str):
        self.models = _DummyModels(response_text)


def _patch_genai_client(monkeypatch, response_text: str):
    monkeypatch.setattr("services.gemini_service.genai.Client", lambda api_key: _DummyClient(response_text))


def test_is_available_returns_false_without_api_key(monkeypatch):
    monkeypatch.setattr("services.gemini_service.settings.GEMINI_API_KEY", "")
    service = GeminiService()

    assert service.is_available() is False
    assert service.analyze_stock_news("AAPL", "Apple") is None


def test_analyze_stock_news_parses_json(monkeypatch):
    monkeypatch.setattr("services.gemini_service.settings.GEMINI_API_KEY", "fake-key")
    payload = """{
        "headline": "Momentum building",
        "summary": "Upward trend and record earnings",
        "sentiment": "POSITIVE",
        "sentiment_score": 0.85,
        "relevance": 92
    }"""
    _patch_genai_client(monkeypatch, payload)

    service = GeminiService()
    news = service.analyze_stock_news("AAPL", "Apple Inc.")

    assert news is not None
    assert news.sentiment == Sentiment.POSITIVE
    assert pytest.approx(news.sentiment_score) == 0.85
    assert news.relevance == 92


def test_analyze_stock_news_uses_fallback_for_invalid_json(monkeypatch):
    monkeypatch.setattr("services.gemini_service.settings.GEMINI_API_KEY", "fake-key")
    _patch_genai_client(monkeypatch, "this is not json")

    service = GeminiService()
    news = service.analyze_stock_news("AAPL", "Apple Inc.")

    assert news is not None
    assert news.sentiment == Sentiment.NEUTRAL
    assert news.sentiment_score == 0.0


def test_get_trading_recommendation_parses_json(monkeypatch):
    monkeypatch.setattr("services.gemini_service.settings.GEMINI_API_KEY", "fake-key")
    payload = """{
        "signal": "BUY",
        "confidence": 82,
        "entry_price": 150,
        "target_price": 165,
        "stop_loss": 145,
        "holding_period": "3-5 days",
        "reasoning": "Strong breakout momentum"
    }"""
    _patch_genai_client(monkeypatch, payload)

    service = GeminiService()
    recommendation = service.get_trading_recommendation("MSFT", {}, {})

    assert isinstance(recommendation, dict)
    assert recommendation["signal"] == "BUY"
    assert recommendation["confidence"] == 82


def test_get_market_summary_returns_text(monkeypatch):
    monkeypatch.setattr("services.gemini_service.settings.GEMINI_API_KEY", "fake-key")
    _patch_genai_client(monkeypatch, "Market mood is positive across the board.")

    service = GeminiService()
    summary = service.get_market_summary([
        {"symbol": "AAPL", "current_price": 200, "change_percent": 1.5}
    ])

    assert isinstance(summary, str)
    assert "positive" in summary.lower()