"""
Entry point for running as module: python -m video_compressor

Supports both CLI, GUI and API modes:
  python -m video_compressor input.mp4          # CLI mode
  python -m video_compressor --gui               # GUI mode
  python -m video_compressor --api               # API mode
"""

import sys


def main():
    if "--gui" in sys.argv:
        try:
            from .gui.app import run_gui

            run_gui()
        except ImportError:
            print(
                "Error: customtkinter is required for GUI mode. "
                "Install it with: pip install customtkinter"
            )
            sys.exit(1)
    elif "--api" in sys.argv:
        try:
            from .api import create_app
            
            app = create_app()
            port = 5000
            if "--port" in sys.argv:
                idx = sys.argv.index("--port")
                if idx + 1 < len(sys.argv):
                    port = int(sys.argv[idx + 1])
            
            print(f"Starting API server on port {port}...")
            app.run(host="127.0.0.1", port=port, debug=False)
        except ImportError as e:
            print(f"Error: Flask and Flask-CORS are required for API mode. {e}")
            sys.exit(1)
    else:
        from .cli import main as cli_main

        cli_main()


if __name__ == "__main__":
    main()
