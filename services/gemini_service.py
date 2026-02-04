"""Gemini AI service for news analysis and insights."""

from google import genai
from typing import Optional, List, Dict
from datetime import datetime
from models.trading_signal import NewsAnalysis, Sentiment
from config.settings import settings
import json

DEFAULT_GEMINI_MODEL = "gemini-pro"


class GeminiService:
    """Service for Gemini AI interactions."""
    
    def __init__(self):
        """Initialize Gemini service."""
        self.api_key = settings.GEMINI_API_KEY
        self.client = None
        
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
                print("✅ Gemini AI initialized successfully")
            except Exception as e:
                print(f"❌ Error initializing Gemini: {str(e)}")
                self.client = None
        else:
            print("⚠️  Gemini API key not configured")
    
    def is_available(self) -> bool:
        """Check if Gemini service is available."""
        return self.client is not None
    
    def analyze_stock_news(self, symbol: str, company_name: str) -> Optional[NewsAnalysis]:
        """
        Analyze news and sentiment for a stock with high-dimensional data points.
        """
        if not self.is_available():
            return None
        
        try:
            prompt = f"""Analyze the recent market news for {company_name} ({symbol}).
Consider macro events (Geopolitics/War/FOMC) and distinguish between 'Signal' and 'Noise'.

Please provide:
1. A brief headline (max 15 words)
2. A concise summary of developments (max 100 words)
3. Overall sentiment: POSITIVE, NEGATIVE, or NEUTRAL
4. Sentiment score from -1 (very negative) to +1 (very positive)
5. Relevance score from 0-100 (impact likelihood)
6. Macro Impact: Does this headline represent a broader market shift (War, Recession, etc)?

Format your response as JSON:
{{
    "headline": "...",
    "summary": "...",
    "sentiment": "POSITIVE|NEGATIVE|NEUTRAL",
    "sentiment_score": 0.5,
    "relevance": 75,
    "macro_impact": true/false
}}"""
            
            response = self.client.models.generate_content(
                model=DEFAULT_GEMINI_MODEL,
                contents=prompt
            )
            text = response.text.strip()
            
            # Try to extract JSON from response
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            data = json.loads(text)
            
            news = NewsAnalysis(
                symbol=symbol,
                headline=data.get("headline", "Market Analysis"),
                summary=data.get("summary", "No summary available"),
                sentiment=Sentiment(data.get("sentiment", "NEUTRAL")),
                sentiment_score=float(data.get("sentiment_score", 0)),
                relevance=float(data.get("relevance", 50)),
                source="Gemini AI",
                timestamp=datetime.now()
            )
            
            return news
            
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return self._fallback_news_analysis(symbol, response.text if 'response' in locals() else "")
        except Exception as e:
            print(f"Error analyzing news for {symbol}: {str(e)}")
            return None
    
    def _fallback_news_analysis(self, symbol: str, text: str) -> NewsAnalysis:
        """Create fallback news analysis from text."""
        # Simple sentiment detection
        positive_words = ["positive", "bullish", "growth", "surge", "gain", "strong", "up"]
        negative_words = ["negative", "bearish", "decline", "drop", "fall", "weak", "down"]
        
        text_lower = text.lower()
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if pos_count > neg_count:
            sentiment = Sentiment.POSITIVE
            score = 0.5
        elif neg_count > pos_count:
            sentiment = Sentiment.NEGATIVE
            score = -0.5
        else:
            sentiment = Sentiment.NEUTRAL
            score = 0.0
        
        return NewsAnalysis(
            symbol=symbol,
            headline=f"Market Analysis for {symbol}",
            summary=text[:200] if text else "Analysis in progress...",
            sentiment=sentiment,
            sentiment_score=score,
            relevance=50,
            source="Gemini AI",
            timestamp=datetime.now()
        )
    
    def get_trading_recommendation(self, symbol: str, stock_data: Dict, indicators: Dict) -> Optional[Dict]:
        """
        Get AI-powered trading recommendation.
        
        Args:
            symbol: Stock ticker symbol
            stock_data: Current stock data
            indicators: Technical indicators
        
        Returns:
            Dictionary with recommendation details
        """
        if not self.is_available():
            return None
        
        try:
            prompt = f"""As a swing trading analyst, analyze {symbol} and provide a recommendation.

Current Data:
- Price: ${stock_data.get('current_price', 'N/A')}
- Change: {stock_data.get('change_percent', 'N/A')}%
- Volume: {stock_data.get('volume', 'N/A')}
- RSI: {indicators.get('rsi', 'N/A')}
- MACD: {indicators.get('macd', 'N/A')}
- Trend: {indicators.get('trend', 'N/A')}

Provide swing trading recommendation (2-10 day timeframe):
1. Signal: BUY, SELL, or HOLD
2. Confidence: 0-100
3. Entry price suggestion
4. Target price (5-10% profit)
5. Stop loss (3-5% loss)
6. Expected holding period
7. Brief reasoning (max 100 words)

Format as JSON:
{{
    "signal": "BUY|SELL|HOLD",
    "confidence": 75,
    "entry_price": 175.50,
    "target_price": 185.00,
    "stop_loss": 170.00,
    "holding_period": "3-5 days",
    "reasoning": "..."
}}"""
            
            response = self.client.models.generate_content(
                model=DEFAULT_GEMINI_MODEL,
                contents=prompt
            )
            text = response.text.strip()
            
            # Extract JSON
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            recommendation = json.loads(text)
            return recommendation
            
        except Exception as e:
            print(f"Error getting recommendation for {symbol}: {str(e)}")
            return None
    
    def get_market_summary(self, stocks_data: List[Dict]) -> str:
        """
        Get overall market summary for multiple stocks.
        
        Args:
            stocks_data: List of stock data dictionaries
        
        Returns:
            Market summary text
        """
        if not self.is_available():
            return "AI analysis not available. Please configure GEMINI_API_KEY."
        
        try:
            symbols = [s.get('symbol', '') for s in stocks_data[:5]]  # Limit to 5 stocks
            data_summary = "\n".join([
                f"- {s.get('symbol')}: ${s.get('current_price', 'N/A')} ({s.get('change_percent', 0):+.2f}%)"
                for s in stocks_data[:5]
            ])
            
            prompt = f"""Provide a brief market summary for these stocks:

{data_summary}

Give a 2-3 sentence overview of the market mood and any standout opportunities.
Be concise and actionable."""
            
            response = self.client.models.generate_content(
                model=DEFAULT_GEMINI_MODEL,
                contents=prompt
            )
            return response.text.strip()
            
        except Exception as e:
            print(f"Error generating market summary: {str(e)}")
            return "Unable to generate market summary at this time."
    
    def explain_indicator(self, indicator_name: str, value: float) -> str:
        """
        Explain what a technical indicator value means.
        
        Args:
            indicator_name: Name of the indicator
            value: Current value
        
        Returns:
            Explanation text
        """
        if not self.is_available():
            return f"{indicator_name}: {value}"
        
        try:
            prompt = f"""Explain in one simple sentence what {indicator_name} value of {value} means for a swing trader.
Be concise and practical."""
            
            response = self.client.models.generate_content(
                model=DEFAULT_GEMINI_MODEL,
                contents=prompt
            )
            return response.text.strip()
            
        except Exception as e:
            return f"{indicator_name}: {value}"
