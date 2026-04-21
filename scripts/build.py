"""
AmeCompression build script for creating standalone executables with PyInstaller.

Usage:
    python scripts/build.py              # Build directory mode (default)
    python scripts/build.py --onefile    # Build single-file mode
    python scripts/build.py --with-ffmpeg # Bundle FFmpeg from bin/ directory
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SPEC_FILE = PROJECT_ROOT / "AmeCompression.spec"
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
BIN_DIR = PROJECT_ROOT / "bin"


def clean():
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    print("Cleaned previous build artifacts.")


def build(onefile: bool = False, with_ffmpeg: bool = False):
    clean()

    cmd = [sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm"]

    if onefile:
        cmd.append("--onefile")
    else:
        cmd.append("--onedir")

    if with_ffmpeg and BIN_DIR.exists():
        ffmpeg_exe = BIN_DIR / "ffmpeg.exe"
        ffprobe_exe = BIN_DIR / "ffprobe.exe"
        if ffmpeg_exe.exists() and ffprobe_exe.exists():
            cmd.extend(["--add-binary", f"{ffmpeg_exe};bin"])
            cmd.extend(["--add-binary", f"{ffprobe_exe};bin"])
            print(f"Bundling FFmpeg from {BIN_DIR}")
        else:
            print("Warning: bin/ directory exists but ffmpeg.exe/ffprobe.exe not found.")

    cmd.append(str(SPEC_FILE))

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))

    if result.returncode == 0:
        print("\nBuild completed successfully!")
        print(f"Output directory: {DIST_DIR}")
        if not onefile and with_ffmpeg:
            target_bin = DIST_DIR / "AmeCompression" / "bin"
            if target_bin.exists():
                print(f"FFmpeg bundled at: {target_bin}")
    else:
        print(f"\nBuild failed with exit code {result.returncode}")
        sys.exit(result.returncode)


def main():
    parser = argparse.ArgumentParser(description="Build AmeCompression executable")
    parser.add_argument("--onefile", action="store_true", help="Build as single .exe file")
    parser.add_argument(
        "--with-ffmpeg", action="store_true", help="Bundle FFmpeg from bin/ directory"
    )
    args = parser.parse_args()

    if not SPEC_FILE.exists():
        print(f"Error: Spec file not found: {SPEC_FILE}")
        sys.exit(1)

    build(onefile=args.onefile, with_ffmpeg=args.with_ffmpeg)


if __name__ == "__main__":
    main()
