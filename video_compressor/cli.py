"""
Command-line interface for video/audio compression.
"""

import argparse
import sys

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
from .utils import get_file_type
from .video import analyze_media, compress_video


def main():
    """Main entry point for the CLI."""
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

    parser.add_argument("input", nargs="?", help="Input video file path")
    parser.add_argument(
        "-o",
        "--output",
        help="Output video file path (default: input_compressed.ext)",
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

    # Get input file path (prompt if not provided)
    input_path = args.input
    if input_path is None:
        input_path = input("Enter the path to the file to compress: ").strip()
        if not input_path:
            print("Error: Input file path not specified.")
            sys.exit(1)

    # Remove surrounding double quotes
    input_path = input_path.strip('"')

    # Handle --analyze option
    if args.analyze:
        analyze_media(
            input_path=input_path,
            ffmpeg_path=ffmpeg_path,
            ffprobe_path=ffprobe_path,
        )
        return

    # Determine file type
    file_type = get_file_type(input_path)

    if file_type == "audio":
        # Audio file compression (to MP3)
        compress_audio(
            input_path=input_path,
            output_path=args.output,
            bitrate=args.audio_bitrate,
            volume_gain=args.volume_gain,
            denoise=args.denoise,
            analyze_only=args.analyze_volume,
            ffmpeg_path=ffmpeg_path,
            ffprobe_path=ffprobe_path,
        )
    elif file_type == "video":
        # Video file compression
        # Validate CRF value
        if not CRF_MIN <= args.crf <= CRF_MAX:
            print(f"Error: CRF must be between {CRF_MIN} and {CRF_MAX}")
            sys.exit(1)

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
            output_path=args.output,
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
        print("Error: Unsupported file type. Supported formats:")
        print(f"  Video: {', '.join(sorted(VIDEO_EXTENSIONS))}")
        print(f"  Audio: {', '.join(sorted(AUDIO_EXTENSIONS))}")
        sys.exit(1)


if __name__ == "__main__":
    main()
