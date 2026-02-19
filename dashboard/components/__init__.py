"""Dashboard components package."""

from .market_overview      import layout as market_overview_layout,      register_callbacks as market_overview_callbacks
from .trading_signals      import layout as trading_signals_layout,      register_callbacks as trading_signals_callbacks
from .day_trading_page     import layout as day_trading_layout,          register_callbacks as day_trading_callbacks
from .swing_trading_page   import layout as swing_trading_layout,        register_callbacks as swing_trading_callbacks
from .portfolio_management import layout as portfolio_layout,            register_callbacks as portfolio_callbacks
from .news_analysis        import layout as news_analysis_layout,        register_callbacks as news_analysis_callbacks
from .backtest_page        import layout as backtest_layout,             register_callbacks as backtest_callbacks
from .charts               import layout as charts_layout,               register_callbacks as charts_callbacks
from .news_controller_page import layout as news_controller_layout,      register_callbacks as news_controller_callbacks
from .beginner_guide_page  import layout as beginner_guide_layout,       register_callbacks as beginner_guide_callbacks
from .backtest_widget      import backtest_panel_layout,                 register_backtest_callbacks

__all__ = [
    "market_overview_layout",   "market_overview_callbacks",
    "trading_signals_layout",   "trading_signals_callbacks",
    "day_trading_layout",       "day_trading_callbacks",
    "swing_trading_layout",     "swing_trading_callbacks",
    "portfolio_layout",         "portfolio_callbacks",
    "news_analysis_layout",     "news_analysis_callbacks",
    "backtest_layout",          "backtest_callbacks",
    "charts_layout",            "charts_callbacks",
    "news_controller_layout",   "news_controller_callbacks",
    "beginner_guide_layout",    "beginner_guide_callbacks",
    "backtest_panel_layout",    "register_backtest_callbacks",
]
