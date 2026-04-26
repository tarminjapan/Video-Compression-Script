"""AmeCompression build script for creating standalone executables with PyInstaller.

Usage:
    uv run scripts/build.py              # Build directory mode (default)
    uv run scripts/build.py --onefile    # Build single-file mode
    uv run scripts/build.py --with-ffmpeg # Bundle FFmpeg from bin/ directory
"""

import argparse
import os
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

    main_script = PROJECT_ROOT / "run.py"
    cmd = [sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm"]

    if onefile:
        cmd.append("--onefile")
    else:
        cmd.append("--onedir")

    cmd.extend(["--name", "ame-compression-backend"])

    # Add hidden imports needed for dynamic imports in the backend
    for hidden in ["backend", "flask", "flask_cors"]:
        cmd.extend(["--hidden-import", hidden])

    # Exclude unnecessary modules to reduce size
    for exclude in ["customtkinter", "tkinter", "windnd"]:
        cmd.extend(["--exclude-module", exclude])

    # Add icon if it exists
    icon_path = PROJECT_ROOT / "assets" / "icon.ico"
    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])

    if with_ffmpeg and BIN_DIR.exists():
        ffmpeg_name = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
        ffprobe_name = "ffprobe.exe" if sys.platform == "win32" else "ffprobe"
        ffmpeg_exe = BIN_DIR / ffmpeg_name
        ffprobe_exe = BIN_DIR / ffprobe_name
        if ffmpeg_exe.exists() and ffprobe_exe.exists():
            cmd.extend(["--add-binary", f"{ffmpeg_exe}{os.pathsep}bin"])
            cmd.extend(["--add-binary", f"{ffprobe_exe}{os.pathsep}bin"])
            print(f"Bundling FFmpeg from {BIN_DIR}")
        else:
            print(f"Warning: bin/ directory exists but {ffmpeg_name}/{ffprobe_name} not found.")

    cmd.append(str(main_script))

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT), check=False)

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
