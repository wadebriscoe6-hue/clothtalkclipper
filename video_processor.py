import subprocess
import os
import shutil

def check_ffmpeg():
    return shutil.which("ffmpeg") is not None

def get_video_duration(input_path):
    cmd = [
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration", "-of",
        "default=noprint_wrappers=1:nokey=1", input_path
    ]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return float(result.stdout.strip())
    except Exception:
        return 0.0

def process_video_clip(input_path, output_path, start_sec, end_sec, style="blur_bg", top_title="", bottom_subtitle=""):
    duration = end_sec - start_sec
    if duration <= 0:
        raise ValueError("End time must be greater than start time.")

    if style == "blur_bg":
        filter_complex = (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:5[bg];"
            "[0:v]scale=1080:-2[fg];"
            "[bg][fg]overlay=(W-w)/2:(H-h)/2[vtemp]"
        )
        current_v = "[vtemp]"
    else:
        filter_complex = "[0:v]scale=-2:1920,crop=1080:1920[vtemp]"
        current_v = "[vtemp]"

    text_filters = []
    if top_title:
        escaped_title = top_title.replace("'", "").replace(":", "").replace("\\", "")
        text_filters.append(
            f"drawtext=text='{escaped_title}':fontcolor=yellow:fontsize=52:box=1:boxcolor=black@0.6:boxborderw=10:x=(w-text_w)/2:y=240"
        )
    if bottom_subtitle:
        escaped_sub = bottom_subtitle.replace("'", "").replace(":", "").replace("\\", "")
        text_filters.append(
            f"drawtext=text='{escaped_sub}':fontcolor=white:fontsize=44:box=1:boxcolor=black@0.7:boxborderw=8:x=(w-text_w)/2:y=h-350"
        )

    if text_filters:
        filter_complex += f";{current_v}" + ",".join(text_filters) + "[vout]"
        map_v = "[vout]"
    else:
        map_v = current_v

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_sec),
        "-i", input_path,
        "-t", str(duration),
        "-filter_complex", filter_complex,
        "-map", map_v,
        "-map", "0:a?",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        output_path
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg error: {result.stderr}")
    return output_path
