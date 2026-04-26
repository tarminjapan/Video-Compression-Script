"""Entry point for running as module: uv run python -m video_compressor

Starts the API server for the GUI application.
"""

import argparse
import sys

try:
    from waitress import serve
except ImportError:
    # We allow this to fail here as it might be dev mode where waitress isn't needed
    # or the error will be caught in the main try-except block
    serve = None

from .api import create_app


def main():
    parser = argparse.ArgumentParser(description="AmeCompression API Server")
    parser.add_argument(
        "--port", type=int, default=5000, help="Port for API server (default: 5000)"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="prod",
        choices=["dev", "prod", "test"],
        help="API configuration mode (default: prod)",
    )

    args = parser.parse_args()

    try:
        app = create_app(config_name=args.config)
        print(f"Starting AmeCompression API server on port {args.port} (config: {args.config})...")

        if args.config == "dev":
            # Flask development server
            app.run(host="127.0.0.1", port=args.port, debug=True)
        else:
            # Production-ready WSGI server
            if serve is None:
                raise ImportError("waitress is required for production mode")

            print(f"Serving on http://127.0.0.1:{args.port}")
            serve(app, host="127.0.0.1", port=args.port)

    except ImportError as e:
        print(f"Error: Required dependencies for API mode not found. {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting API server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
