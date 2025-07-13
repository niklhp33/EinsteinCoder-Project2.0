import logging
import subprocess
import os
import shlex
import math
from typing import List, Tuple, Optional, Any
import shutil

from utils.shell_utils import run_shell_command
from utils.video_utils import get_video_duration

logger = logging.getLogger(__name__)

def get_video_dimensions(video_path: str) -> Optional[Tuple[int, int]]:
    """
    Gets the width and height of a video file using ffprobe.
    """
    cmd = ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
           '-show_entries', 'stream=width,height', '-of', 'csv=p=0:s=x',
           shlex.quote(video_path)]
    
    stdout, stderr, returncode = run_shell_command(cmd, check_error=False)
    
    if returncode != 0:
        logger.warning(f"ffprobe failed to get dimensions for {video_path}: {stderr}")
        return None
    
    try:
        dimensions_str = stdout.strip()
        width, height = map(int, dimensions_str.split('x'))
        return width, height
    except ValueError:
        logger.warning(f"Could not parse dimensions from ffprobe output for {video_path}: {stdout}")
        return None

def concatenate_videos(
    video_paths: List[str],
    output_path: str,
    target_width: int,
    target_height: int,
    target_duration: float,
    transition: str = 'fade',
    transition_duration: float = 0.5,
    randomize_order: bool = True
) -> bool:
    """
    Concatenates a list of video clips with or without transitions using FFmpeg.
    Each clip is scaled/cropped to fit target_width/height.
    The total duration of the concatenated video is adjusted to be close to target_duration.
    """
    if not video_paths:
        logger.error("No video paths provided for concatenation.")
        return False

    logger.info(f"Concatenating {len(video_paths)} videos with {transition} transitions to {output_path}")

    # Determine target resolution for scaling
    scale_crop_filter = (
        f"scale={target_width}:{target_height}:force_original_aspect_ratio=increase,"
        f"crop={target_width}:{target_height},setsar=1,fps=25" # Standardize FPS here
    )

    # Convert transition name to lowercase for FFmpeg compatibility
    normalized_transition = transition.lower()
    
    # If no transition, use simple concat demuxer or a basic concat filter
    if normalized_transition == 'none' or len(video_paths) == 1:
        logger.info("Performing simple concatenation without transitions.")
        
        # Ensure all input video streams are processed for consistent dimensions/fps/audio before concat
        filter_complex_parts = []
        input_streams_for_complex = []
        
        for i, video_path in enumerate(video_paths):
            input_streams_for_complex.extend(['-i', shlex.quote(video_path)])
            filter_complex_parts.append(f"[{i}:v]{scale_crop_filter}[v{i}];[{i}:a]aresample=async=1[a{i}]")

        # Build the simple concat filter string
        concat_video_inputs = "".join([f"[v{i}]" for i in range(len(video_paths))])
        concat_audio_inputs = "".join([f"[a{i}]" for i in range(len(video_paths))])
        
        filter_complex_parts.append(f"{concat_video_inputs}concat=n={len(video_paths)}:v=1:a=0[v_out]")
        filter_complex_parts.append(f"{concat_audio_inputs}concat=n={len(video_paths)}:v=0:a=1[a_out]")

        full_filter_complex_str = ";".join(filter_complex_parts)

        cmd = ['ffmpeg', '-y'] + input_streams_for_complex + [
               '-filter_complex', full_filter_complex_str,
               '-map', '[v_out]', '-map', '[a_out]',
               '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
               '-pix_fmt', 'yuv420p',
               '-c:a', 'aac', '-b:a', '192k',
               '-t', str(target_duration),
               shlex.quote(output_path)]
        
        stdout, stderr, returncode = run_shell_command(cmd, check_error=False, timeout=600)
        
        if returncode != 0:
            logger.error(f"FFmpeg simple concatenation failed: {stderr}")
            return False
        logger.info(f"Videos concatenated successfully (no transitions) to {output_path}.")
        return True

    # --- Complex filtergraph for transitions (if transition is not 'none' and multiple videos) ---
    filter_complex = []
    input_streams = []
    
    effective_clip_durations = []
    total_raw_duration = 0.0
    for path in video_paths:
        duration = get_video_duration(path)
        if duration is None:
            logger.error(f"Could not get duration for video clip: {path}. Cannot concatenate.")
            return False
        effective_clip_durations.append(duration)
        total_raw_duration += duration

    # Scale and crop each input video to target dimensions and then assign labels
    for i, video_path in enumerate(video_paths):
        filter_complex.append(
            f"[{i}:v]{scale_crop_filter}[v{i}]"
        )
        filter_complex.append(f"[{i}:a]aresample=async=1[a{i}]")
        input_streams.extend(['-i', shlex.quote(video_path)])

    video_concat_filters = []
    audio_concat_filters = []
    current_total_effective_duration = 0.0
    
    for i in range(len(video_paths)):
        if i == 0:
            current_video_stream = f"[v0]"
            current_audio_stream = f"[a0]"
            current_total_effective_duration += effective_clip_durations[i]
        else:
            xfade_offset = current_total_effective_duration - transition_duration
            
            # CRITICAL FIX: Ensure the transition name is robustly quoted for FFmpeg.
            # Using shlex.quote around the f-string that contains the single-quoted transition name.
            video_concat_filters.append(
                f"{current_video_stream}[v{i}]xfade=transition={shlex.quote(normalized_transition)}:duration={transition_duration}:offset={xfade_offset}[v_out{i}]"
            )
            audio_concat_filters.append(
                f"{current_audio_stream}[a{i}]acrossfade=d={transition_duration}[a_out{i}]"
            )
            current_video_stream = f"[v_out{i}]"
            current_audio_stream = f"[a_out{i}]"
            current_total_effective_duration += effective_clip_durations[i] - transition_duration

    final_video_stream = current_video_stream
    final_audio_stream = current_audio_stream

    filter_complex_str = ";".join(filter_complex + video_concat_filters + audio_concat_filters)

    output_options = [
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', '23',
        '-pix_fmt', 'yuv420p',
        '-movflags', '+faststart',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-map', final_video_stream,
        '-map', final_audio_stream,
        '-t', str(target_duration)
    ]

    cmd = ['ffmpeg', '-y'] + input_streams + [
        '-filter_complex', filter_complex_str
    ] + output_options + [shlex.quote(output_path)]

    logger.info(f"Running FFmpeg concat command: {' '.join(cmd)}")
    stdout, stderr, returncode = run_shell_command(cmd, check_error=False, timeout=600)

    if returncode != 0:
        logger.error(f"FFmpeg video concatenation failed: {stderr}")
        return False
    
    logger.info(f"Videos concatenated successfully to {output_path}.")
    return True


def add_audio_to_video(video_path: str, audio_path: str, output_path: str) -> bool:
    """
    Adds an audio track to a video file. If video has audio, it's replaced.
    """
    logger.info(f"Adding audio {audio_path} to video {video_path}...")
    cmd = [
        'ffmpeg', '-y',
        '-i', shlex.quote(video_path),
        '-i', shlex.quote(audio_path),
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-map', '0:v:0',
        '-map', '1:a:0',
        '-shortest',
        shlex.quote(output_path)
    ]
    stdout, stderr, returncode = run_shell_command(cmd, check_error=False, timeout=300)
    if returncode != 0:
        logger.error(f"Failed to add audio to {video_path}: {stderr}")
        return False
    logger.info(f"Audio added to video. Output: {output_path}.")
    return True

def add_subtitles_to_video(
    video_path: str,
    subtitle_file_path: str,
    output_path: str,
    font_path: str,
    font_size: int,
    font_color: str,
    outline_color: str,
    outline_width: int,
    position: str # 'Top', 'Bottom', 'Center'
) -> bool:
    """
    Adds burnt-in subtitles to a video using FFmpeg and a .ass subtitle file.
    """
    logger.info(f"Adding subtitles from {subtitle_file_path} to {video_path}...")

    quoted_font_path = shlex.quote(font_path)
    
    cmd = [
        'ffmpeg', '-y',
        '-i', shlex.quote(video_path),
        '-vf', f"subtitles={shlex.quote(subtitle_file_path)}:fontsdir={os.path.dirname(quoted_font_path)}", # Specify fontsdir explicitly
        '-c:a', 'copy',
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '23',
        '-pix_fmt', 'yuv420p',
        shlex.quote(output_path)
    ]
    logger.info(f"Running FFmpeg subtitles command: {' '.join(cmd)}")
    stdout, stderr, returncode = run_shell_command(cmd, check_error=False, timeout=300)

    if returncode != 0:
        logger.error(f"FFmpeg failed to add subtitles: {stderr}")
        return False
    
    logger.info(f"Subtitles added to video. Output: {output_path}.")
    return True

def escape_ffmpeg_text(text: str) -> str:
    """
    Escapes special characters in text for FFmpeg's drawtext filter.
    """
    text = text.replace("'", "\\'")
    text = text.replace("\\", "\\\\")
    text = text.replace(":", "\\:")
    text = text.replace(",", "\\,")
    text = text.replace(";", "\\;")
    text = text.replace("[", "\\[")
    text = text.replace("]", "\\]")
    return text
