#!/usr/bin/env python3
"""
FFmpegを使用した動画圧縮スクリプト
- 最大解像度: 2K (2560x1440)
- コーデック: SVT-AV1 (高速AV1コーデック、CRF 25)
- 音声: MP3 (最大192kbps)
"""

import argparse
import subprocess
import sys
from pathlib import Path


def get_video_info(video_path):
    """
    ffprobeを使用して動画情報を取得

    戻り値:
        dict: 動画の幅、高さ
    """
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-of",
        "csv=s=x:p=0",
        str(video_path),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        if output:
            width, height = map(int, output.split("x"))
            return {"width": width, "height": height}
    except subprocess.CalledProcessError as e:
        print(f"動画情報の取得エラー: {e.stderr}")
        sys.exit(1)

    return None


def calculate_scaled_resolution(width, height, max_width=2560, max_height=1440):
    """
    アスペクト比を維持したまま縮小後の解像度を計算

    引数:
        width (int): 元の幅
        height (int): 元の高さ
        max_width (int): 許可される最大幅 (2K = 2560)
        max_height (int): 許可される最大高さ (2K = 1440)

    戻り値:
        tuple: (縮小後の幅, 縮小後の高さ) または 縮小不要な場合はNone
    """
    # 縮小が必要か確認
    if width <= max_width and height <= max_height:
        return None

    # 縮小比率を計算
    width_ratio = max_width / width
    height_ratio = max_height / height

    # 両方の制約に収まる小さい比率を使用
    scale_ratio = min(width_ratio, height_ratio)

    # 新しい寸法を計算（エンコード品質向上のため偶数にする）
    scaled_width = max(2, int(width * scale_ratio) // 2 * 2)
    scaled_height = max(2, int(height * scale_ratio) // 2 * 2)

    return (scaled_width, scaled_height)


def compress_video(input_path, output_path=None, crf=25, audio_bitrate="192k"):
    """
    FFmpegとAV1コーデックを使用して動画を圧縮

    引数:
        input_path (str): 入力動画ファイルのパス
        output_path (str): 出力動画ファイルのパス（オプション）
        crf (int): AV1のCRF値（デフォルト: 25）
        audio_bitrate (str): 音声ビットレート（デフォルト: 192k）
    """
    input_path = Path(input_path)

    # 入力ファイルを検証
    if not input_path.exists():
        print(f"エラー: 入力ファイル '{input_path}' が存在しません。")
        sys.exit(1)

    # デフォルトの出力パスを設定
    if output_path is None:
        output_path = (
            input_path.parent / f"{input_path.stem}_compressed{input_path.suffix}"
        )
    else:
        output_path = Path(output_path)

    # 動画情報を取得
    print(f"動画を分析中: {input_path}")
    video_info = get_video_info(input_path)

    if not video_info:
        print("エラー: 動画情報を取得できませんでした。")
        sys.exit(1)

    original_width = video_info["width"]
    original_height = video_info["height"]
    print(f"元の解像度: {original_width}x{original_height}")

    # 必要に応じて縮小後の解像度を計算
    scaled_res = calculate_scaled_resolution(original_width, original_height)

    # ffmpegコマンドを構築
    cmd = ["ffmpeg", "-i", str(input_path), "-y"]  # -yで出力を上書き

    # 必要に応じて動画スケーリングフィルタを追加
    if scaled_res:
        scaled_width, scaled_height = scaled_res
        print(f"アスペクト比を維持して {scaled_width}x{scaled_height} に縮小中")
        cmd.extend(["-vf", f"scale={scaled_width}:{scaled_height}"])
    else:
        print("縮小は不要です（解像度が既に2K以下）")

    # ビデオコーデック設定（SVT-AV1）
    cmd.extend(
        [
            "-c:v",
            "libsvtav1",  # 高速AV1コーデック（SVT-AV1）
            "-crf",
            str(crf),  # 品質設定（低いほど高品質、高いほど小サイズ）
            "-b:v",
            "0",  # ビットレートベースのエンコーディングを無効化（CRFモード）
            "-preset",
            "6",  # エンコード速度プリセット（0-13、高いほど高速）
        ]
    )

    # オーディオコーデック設定（MP3）
    cmd.extend(
        [
            "-c:a",
            "libmp3lame",  # MP3コーデック
            "-b:a",
            audio_bitrate,  # 音声ビットレート
        ]
    )

    # 出力ファイル
    cmd.append(str(output_path))

    # 参考用にコマンドを表示
    print(f"\nFFmpegコマンド: {' '.join(cmd)}\n")
    print("圧縮を開始します...")

    # ffmpegコマンドを実行
    process = None
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,  # stdinを閉じてブロックを防止
            encoding="utf-8",
            errors="replace",
        )

        # リアルタイムで進捗を表示
        if process.stdout:
            for line in process.stdout:
                print(line, end="")

        process.wait()

        if process.returncode == 0:
            print("\n✓ 圧縮が正常に完了しました！")
            print(f"  出力: {output_path}")

            # 出力ファイルサイズを取得
            output_size = output_path.stat().st_size / (1024 * 1024)  # MB
            input_size = input_path.stat().st_size / (1024 * 1024)  # MB
            compression_ratio = (1 - output_size / input_size) * 100

            print(f"  入力サイズ: {input_size:.2f} MB")
            print(f"  出力サイズ: {output_size:.2f} MB")
            print(f"  圧縮率: {compression_ratio:.1f}% 削減")
        else:
            print(f"\n✗ 圧縮に失敗しました（リターンコード: {process.returncode}）")
            sys.exit(1)

    except FileNotFoundError:
        print(
            "エラー: FFmpegが見つかりません。FFmpegがインストールされ、PATHに追加されていることを確認してください。"
        )
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nユーザーによって圧縮が中断されました。")
        if process is not None:
            process.terminate()
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="FFmpegとAV1コーデックを使用して動画を圧縮",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  %(prog)s input.mp4
  %(prog)s input.mp4 -o output.mp4
  %(prog)s input.mp4 --crf 23 --audio-bitrate 256k
        """,
    )

    parser.add_argument("input", help="入力動画ファイルのパス")
    parser.add_argument(
        "-o",
        "--output",
        help="出力動画ファイルのパス（デフォルト: input_compressed.ext）",
    )
    parser.add_argument(
        "--crf",
        type=int,
        default=25,
        help="AV1 CRF値（0-63、低いほど高品質、高いほど小サイズ、デフォルト: 25）",
    )
    parser.add_argument(
        "--audio-bitrate", default="192k", help="音声ビットレート（デフォルト: 192k）"
    )

    args = parser.parse_args()

    # CRF値を検証
    if not 0 <= args.crf <= 63:
        print("エラー: CRFは0から63の間でなければなりません")
        sys.exit(1)

    # 圧縮を実行
    compress_video(
        input_path=args.input,
        output_path=args.output,
        crf=args.crf,
        audio_bitrate=args.audio_bitrate,
    )


if __name__ == "__main__":
    main()
