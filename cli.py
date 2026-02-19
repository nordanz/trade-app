"""CLI entry point for the eSignal dashboard."""

import sys
import subprocess
from pathlib import Path


def main():
    """Launch the Streamlit dashboard."""
    # Get the path to the app.py file
    app_path = Path(__file__).parent / "dashboard" / "app.py"
    
    if not app_path.exists():
        print(f"❌ Error: app.py not found at {app_path}")
        sys.exit(1)
    
    print("🚀 Launching eSignal Dashboard...")
    print(f"📂 Running app from: {app_path}")
    
    # Run streamlit with the app
    try:
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", str(app_path)],
            check=False
        )
    except KeyboardInterrupt:
        print("\n👋 Dashboard closed")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error launching dashboard: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
