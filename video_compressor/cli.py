"""
Command-line interface for video/audio compression.
"""

import argparse
import sys
from pathlib import Path

from .audio import compress_audio
from .config import (
    AUDIO_EXTENSIONS,
    CRF_MAX,
    CRF_MIN,
    DEFAULT_AUDIO_BITRATE,
    DEFAULT_CRF,
    DEFAULT_DENOISE_LEVEL,
    MAX_FPS,
    VIDEO_EXTENSIONS,
    VIDEO_PRESET,
)
from .ffmpeg import get_ffmpeg_executables
from .utils import get_file_type, parse_input_paths, print_banner
from .video import analyze_media, compress_video

# ANSI color codes for summary
_GREEN = "\033[92m"
_YELLOW = "\033[93m"
_RED = "\033[91m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_RESET = "\033[0m"
_CYAN = "\033[96m"


def resolve_output_path(input_path, output_arg, num_files):
    """
    Resolve the output path for a single input file based on --output argument.

    Smart --output logic:
    - No --output: same directory as input, {stem}_compressed{suffix}
    - --output is an existing directory: output inside that directory
    - --output ends with '/' or '\\': treat as directory, create if needed
    - --output is a file path and num_files == 1: use as-is (legacy behavior)
    - --output is a file path and num_files > 1: error

    Args:
        input_path (Path): Input file path
        output_arg (str or None): Value of --output argument
        num_files (int): Total number of input files

    Returns:
        Path or None: Resolved output path (None means use default in compress function)
    """
    if output_arg is None:
        return None

    output_path = Path(output_arg)

    # Case 1: --output is an existing directory
    if output_path.is_dir():
        return output_path / f"{input_path.stem}_compressed{input_path.suffix}"

    # Case 2: --output ends with path separator → treat as directory
    if output_arg.endswith(("/", "\\")):
        output_path.mkdir(parents=True, exist_ok=True)
        return output_path / f"{input_path.stem}_compressed{input_path.suffix}"

    # Case 3: --output looks like a directory (no extension and doesn't exist yet)
    # This handles cases like "output_dir" (no trailing slash, doesn't exist yet)
    if output_path.suffix == "" and not output_path.exists():
        output_path.mkdir(parents=True, exist_ok=True)
        return output_path / f"{input_path.stem}_compressed{input_path.suffix}"

    # Case 4: --output is a specific file path
    if num_files == 1:
        return output_path

    # Case 5: --output is a file path but multiple files → error
    print(
        f"  {_YELLOW}Warning: --output specifies a file but {num_files} input files given.{_RESET}"
    )
    print(f"  {_YELLOW}Use a directory path for --output when processing multiple files.{_RESET}")
    sys.exit(1)


def process_single_file(
    input_path,
    args,
    ffmpeg_path,
    ffprobe_path,
    output_override=None,
):
    """
    Process a single file (compress or analyze).

    Args:
        input_path (str): Path to input file
        args: Parsed argparse namespace
        ffmpeg_path (str): Path to ffmpeg executable
        ffprobe_path (str): Path to ffprobe executable
        output_override (str or None): Override output path for batch processing

    Returns:
        bool: True if successful, False otherwise
    """
    # Determine file type
    file_type = get_file_type(input_path)

    if file_type == "audio":
        compress_audio(
            input_path=input_path,
            output_path=output_override,
            bitrate=args.audio_bitrate,
            volume_gain=args.volume_gain,
            denoise=args.denoise,
            analyze_only=args.analyze_volume,
            ffmpeg_path=ffmpeg_path,
            ffprobe_path=ffprobe_path,
        )
    elif file_type == "video":
        # Validate CRF value
        if not CRF_MIN <= args.crf <= CRF_MAX:
            print(f"Error: CRF must be between {CRF_MIN} and {CRF_MAX}")
            return False

        # Validate FPS value
        max_fps = args.fps
        if max_fps is not None and max_fps > MAX_FPS:
            print(f"Warning: FPS capped to {MAX_FPS} (requested: {max_fps})")
            max_fps = MAX_FPS

        # Determine audio settings
        audio_enabled = not args.no_audio

        # Run compression
        compress_video(
            input_path=input_path,
            output_path=output_override,
            crf=args.crf,
            preset=args.preset,
            audio_bitrate=args.audio_bitrate,
            audio_enabled=audio_enabled,
            max_fps=max_fps,
            resolution=args.resolution,
            volume_gain=args.volume_gain,
            denoise=args.denoise,
            analyze_only=args.analyze_volume,
            ffmpeg_path=ffmpeg_path,
            ffprobe_path=ffprobe_path,
        )
    else:
        print(f"Error: Unsupported file type for '{input_path}'. Supported formats:")
        print(f"  Video: {', '.join(sorted(VIDEO_EXTENSIONS))}")
        print(f"  Audio: {', '.join(sorted(AUDIO_EXTENSIONS))}")
        return False

    return True


def main():
    """Main entry point for the CLI."""
    print_banner()

    parser = argparse.ArgumentParser(
        description="Compress video/audio using FFmpeg (AV1 for video, MP3 for audio)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Video compression
  %(prog)s input.mp4
  %(prog)s input.mp4 -o output.mp4
  %(prog)s input.mp4 --crf 23 --audio-bitrate 256k
  %(prog)s input.mp4 --resolution 1920x1080 --fps 60
  %(prog)s input.mp4 --no-audio

  # Batch processing (multiple files)
  %(prog)s "file1.mp4" "file2.mp4" "file3.mp4"
  %(prog)s file1.mp4 file2.mp4 -o /path/to/output_dir/
  %(prog)s "path with spaces.mp4", another.mp4

  # Audio compression (to MP3)
  %(prog)s music.mp3 --audio-bitrate 128k
  %(prog)s audio.wav --audio-bitrate 192k
  %(prog)s song.flac -o compressed.mp3

  # Volume adjustment
  %(prog)s meeting.mp4 --volume-gain auto
  %(prog)s meeting.mp4 --volume-gain 10dB
  %(prog)s meeting.mp4 --volume-gain 2.0
  %(prog)s audio.mp3 --analyze-volume

  # Noise reduction
  %(prog)s meeting.mp4 --denoise
  %(prog)s meeting.mp4 --denoise 0.3
  %(prog)s meeting.mp4 --volume-gain auto --denoise 0.2
        """,
    )

    parser.add_argument(
        "input",
        nargs="*",
        help="Input file path(s). Multiple files can be specified separated by spaces, commas, or newlines.",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output file or directory path. For multiple files, specify a directory. (default: input_compressed.ext)",
    )
    parser.add_argument(
        "--crf",
        type=int,
        default=DEFAULT_CRF,
        help=f"AV1 CRF value ({CRF_MIN}-{CRF_MAX}, lower = higher quality, higher = smaller size, default: {DEFAULT_CRF})",
    )
    parser.add_argument(
        "--preset",
        type=int,
        default=VIDEO_PRESET,
        help=f"Encoding speed preset (0-13, higher = faster encoding but larger file, default: {VIDEO_PRESET})",
    )
    parser.add_argument(
        "--audio-bitrate",
        default=DEFAULT_AUDIO_BITRATE,
        help=f"Audio bitrate (video: default {DEFAULT_AUDIO_BITRATE}, max 320k | audio/MP3: 32k-320k)",
    )
    parser.add_argument(
        "--no-audio",
        action="store_true",
        help="Disable audio track (audio bitrate option will be ignored)",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=None,
        help=f"Maximum FPS (default: keep original, max: {MAX_FPS})",
    )
    parser.add_argument(
        "--resolution",
        type=str,
        default=None,
        help="Maximum resolution in WxH format (e.g., 1920x1080, default: 3840x2160)",
    )
    parser.add_argument(
        "--volume-gain",
        type=str,
        default=None,
        help="Volume gain: multiplier (e.g., '2.0'), dB (e.g., '10dB'), or 'auto' for automatic adjustment",
    )
    parser.add_argument(
        "--analyze-volume",
        action="store_true",
        help="Analyze volume level and show recommended gain (no compression)",
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Analyze media file and show detailed information (codec, resolution, bitrate, etc.)",
    )
    parser.add_argument(
        "--denoise",
        type=float,
        nargs="?",
        const=DEFAULT_DENOISE_LEVEL,
        default=None,
        help=f"Enable audio noise reduction (level: 0.0-1.0, default: {DEFAULT_DENOISE_LEVEL})",
    )

    args = parser.parse_args()

    # Get FFmpeg executable paths
    ffmpeg_path, ffprobe_path = get_ffmpeg_executables()

    # Collect raw input paths
    raw_inputs = args.input

    # If no inputs via argument, prompt interactively
    if not raw_inputs:
        raw_input = input("Enter the path(s) to the file(s) to compress: ").strip()
        if not raw_input:
            print("Error: Input file path not specified.")
            sys.exit(1)
        raw_inputs = [raw_input]

    # Parse input paths (handles newlines, commas, spaces, quotes)
    input_paths = parse_input_paths(raw_inputs)

    if not input_paths:
        print("Error: No valid input file paths found.")
        sys.exit(1)

    # Handle --analyze option (single file only)
    if args.analyze:
        if len(input_paths) > 1:
            print("Error: --analyze can only be used with a single file.")
            sys.exit(1)
        analyze_media(
            input_path=input_paths[0],
            ffmpeg_path=ffmpeg_path,
            ffprobe_path=ffprobe_path,
        )
        return

    # Single file processing
    if len(input_paths) == 1:
        input_path = input_paths[0]
        success = False
        try:
            success = process_single_file(
                input_path=input_path,
                args=args,
                ffmpeg_path=ffmpeg_path,
                ffprobe_path=ffprobe_path,
                output_override=args.output,
            )
        except SystemExit as e:
            if e.code != 0:
                sys.exit(e.code)
            return
        if not success:
            sys.exit(1)
        return

    # Batch processing (multiple files)
    num_files = len(input_paths)
    print(f"\n  {_BOLD}Batch mode: processing {num_files} files{_RESET}")
    print(f"  {_CYAN}{'─' * 48}{_RESET}")

    successes = []
    failures = []

    for i, input_path in enumerate(input_paths, 1):
        print(f"\n  {_BOLD}[{i}/{num_files}]{_RESET} Processing: {_DIM}{input_path}{_RESET}")
        print(f"  {_CYAN}{'─' * 48}{_RESET}")

        # Resolve output path for this file
        output_path = resolve_output_path(Path(input_path), args.output, num_files)
        output_str = str(output_path) if output_path else None

        try:
            success = process_single_file(
                input_path=input_path,
                args=args,
                ffmpeg_path=ffmpeg_path,
                ffprobe_path=ffprobe_path,
                output_override=output_str,
            )
            if success:
                successes.append(input_path)
            else:
                failures.append(input_path)
        except SystemExit:
            failures.append(input_path)
        except KeyboardInterrupt:
            print(f"\n\n  {_YELLOW}Batch processing interrupted by user.{_RESET}")
            failures.extend(input_paths[i - 1 :])
            break

    # Print batch summary
    print(f"\n  {_CYAN}{'━' * 48}{_RESET}")
    print(f"  {_BOLD}Batch Summary{_RESET}")
    print(f"  {_CYAN}{'─' * 48}{_RESET}")
    total = len(successes) + len(failures)
    print(f"  Total:   {total}")
    print(f"  {_GREEN}Success: {len(successes)}{_RESET}")
    if failures:
        print(f"  {_RED}Failed:  {len(failures)}{_RESET}")
        for f in failures:
            print(f"    {_RED}✗ {_DIM}{f}{_RESET}")
    print(f"  {_CYAN}{'━' * 48}{_RESET}")

    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
