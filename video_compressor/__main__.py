"""
Entry point for running as module: python -m video_compressor

Supports both CLI, GUI and API modes:
  python -m video_compressor input.mp4          # CLI mode
  python -m video_compressor --gui               # GUI mode
  python -m video_compressor --api               # API mode
"""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(description="AmeCompression - Video and Audio Compressor")
    parser.add_argument("--gui", action="store_true", help="Start in GUI mode")
    parser.add_argument("--api", action="store_true", help="Start in API mode")
    parser.add_argument("--port", type=int, default=5000, help="Port for API mode (default: 5000)")
    parser.add_argument("--config", type=str, default="dev", choices=["dev", "prod", "test"], help="API configuration mode")
    
    # Use parse_known_args to avoid failing on CLI-specific arguments
    args, unknown = parser.parse_known_args()

    if args.gui:
        try:
            from .gui.app import run_gui

            run_gui()
        except ImportError:
            print(
                "Error: customtkinter is required for GUI mode. "
                "Install it with: pip install customtkinter"
            )
            sys.exit(1)
    elif args.api:
        try:
            from .api import create_app
            
            app = create_app(config_name=args.config)
            print(f"Starting API server on port {args.port} (config: {args.config})...")
            app.run(host="127.0.0.1", port=args.port, debug=False)
        except ImportError as e:
            print(f"Error: Flask and Flask-CORS are required for API mode. {e}")
            sys.exit(1)
    else:
        # For CLI mode, we let cli_main handle everything
        from .cli import main as cli_main
        cli_main()


if __name__ == "__main__":
    main()
