import logging
import subprocess
import os
import shlex
import math
import random
from typing import List, Tuple, Optional, Any
import shutil

from utils.shell_utils import run_shell_command
from utils.video_utils import get_video_duration # Assuming get_video_duration is in video_utils

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
    randomize_order: bool = False,
    temp_files_dir: str = '/tmp/tiktok_project_runtime/temp_files'
) -> Optional[str]:
    """
    Concatenates multiple video clips into a single video with optional transitions.
    All input videos are scaled and cropped to match target_width/height.
    If the total duration of input videos is less than target_duration, the last video is looped.
    """
    logger.info(f"Concatenating {len(video_paths)} videos to {output_path} with transition '{transition}'.")
    if not video_paths:
        logger.error("No video paths provided for concatenation.")
        return None

    # Ensure temp directory exists
    os.makedirs(temp_files_dir, exist_ok=True)

    # Filter out non-existent paths
    existing_video_paths = [p for p in video_paths if os.path.exists(p)]
    if len(existing_video_paths) != len(video_paths):
        logger.warning(f"Skipped {len(video_paths) - len(existing_video_paths)} non-existent video paths.")
    if not existing_video_paths:
        logger.error("No valid video paths found for concatenation after filtering.")
        return None

    if randomize_order:
        random.shuffle(existing_video_paths)
        logger.info("Video order randomized.")

    # Create a list of scaled/cropped temporary video paths
    temp_scaled_videos = []
    current_total_duration = 0.0

    for i, video_path in enumerate(existing_video_paths):
        temp_output_path = os.path.join(temp_files_dir, f"scaled_clip_{i}.mp4")
        
        # Simple scaling to fit width, then pad/crop height
        scale_filter = f"scale='min({target_width},iw)':'min({target_height},ih)':force_original_aspect_ratio=decrease,pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2"
        
        cmd = [
            'ffmpeg', '-y',
            '-i', shlex.quote(video_path),
            '-vf', scale_filter,
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-pix_fmt', 'yuv420p',
            temp_output_path
        ]
        stdout, stderr, returncode = run_shell_command(cmd, check_error=False, timeout=180)
        if returncode != 0:
            logger.error(f"Failed to scale/crop video {video_path}: {stderr}")
            continue
        temp_scaled_videos.append(temp_output_path)
        current_total_duration += get_video_duration(temp_output_path) or 0.0

    if not temp_scaled_videos:
        logger.error("No videos successfully scaled for concatenation.")
        return None

    # Handle duration mismatch: loop last video if total duration is less than target
    final_clips_for_concat = list(temp_scaled_videos) # Copy the list
    if current_total_duration < target_duration:
        last_clip_path = final_clips_for_concat[-1]
        remaining_duration = target_duration - current_total_duration
        logger.info(f"Total clip duration ({current_total_duration:.2f}s) is less than target ({target_duration:.2f}s). Looping last clip for {remaining_duration:.2f}s.")

        # Create a looped version of the last clip
        temp_looped_clip_path = os.path.join(temp_files_dir, "looped_last_clip.mp4")
        
        # Calculate how many times the last clip needs to loop
        last_clip_duration = get_video_duration(last_clip_path)
        if last_clip_duration and last_clip_duration > 0:
            num_loops = math.ceil(remaining_duration / last_clip_duration)
            
            # Use stream_loop for looping
            loop_cmd = [
                'ffmpeg', '-y',
                '-stream_loop', str(num_loops -1),
                '-i', shlex.quote(last_clip_path),
                '-c', 'copy',
                '-t', str(remaining_duration), # Trim to exact remaining duration
                temp_looped_clip_path
            ]
            stdout, stderr, returncode = run_shell_command(loop_cmd, check_error=False, timeout=180)
            if returncode == 0 and os.path.exists(temp_looped_clip_path):
                final_clips_for_concat.append(temp_looped_clip_path)
                logger.info(f"Looped last clip and added to concatenation list.")
            else:
                logger.warning(f"Failed to loop last clip: {stderr}. Proceeding without looping.")
        else:
            logger.warning("Last clip duration is zero or invalid, cannot loop.")


    # Create a concat list file
    concat_list_path = os.path.join(temp_files_dir, "concat_list.txt")
    with open(concat_list_path, 'w') as f:
        for clip in final_clips_for_concat:
            f.write(f"file '{clip}'\n")

    # FFmpeg concatenation command
    if transition == 'none':
        concat_cmd = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0', # Allows absolute paths
            '-i', concat_list_path,
            '-c', 'copy',
            output_path
        ]
    else:
        # Complex filtergraph for transitions (simplified for example)
        # This part would need significant expansion for real transitions.
        # For 'fade' and 'crossfade', moviepy's concatenate_videoclips handles it better.
        # FFmpeg filtergraph for crossfade:
        # [0:v][1:v]xfade=transition=fade:duration=1:offset=9[v]
        # For simplicity, we'll use basic concatenation and log a warning for complex transitions.
        logger.warning(f"Complex transitions like '{transition}' are not fully implemented via raw FFmpeg concat_videos. Using simple concat.")
        concat_cmd = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_list_path,
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-pix_fmt', 'yuv420p',
            output_path
        ]

    stdout, stderr, returncode = run_shell_command(concat_cmd, check_error=False, timeout=300)

    if returncode != 0:
        logger.error(f"FFmpeg concatenation failed: {stderr}")
        return None

    logger.info(f"Videos concatenated successfully. Output: {output_path}.")

    # Clean up temporary scaled videos and concat list
    for clip in temp_scaled_videos:
        if os.path.exists(clip):
            os.remove(clip)
    if os.path.exists(concat_list_path):
        os.remove(concat_list_path)
    if 'temp_looped_clip_path' in locals() and os.path.exists(temp_looped_clip_path):
        os.remove(temp_looped_clip_path)

    return output_path

def add_audio_to_video(video_path: str, audio_path: str, output_path: str, audio_volume_db: float = 0.0) -> Optional[str]:
    """
    Adds an audio track to a video, replacing any existing audio.
    Also adjusts the volume of the added audio.
    """
    logger.info(f"Adding audio from {audio_path} to {video_path} with volume {audio_volume_db}dB.")
    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        return None
    if not os.path.exists(audio_path):
        logger.error(f"Audio file not found: {audio_path}")
        return None

    # Use -map 0:v to select video stream from first input, -map 1:a to select audio stream from second input
    # -shortest makes the output duration the shortest of the input streams (video or audio)
    # -af "volume=...dB" applies volume filter
    cmd = [
        'ffmpeg', '-y',
        '-i', shlex.quote(video_path),
        '-i', shlex.quote(audio_path),
        '-map', '0:v',
        '-map', '1:a',
        '-c:v', 'copy',
        '-c:a', 'aac', # Encode audio to AAC
        '-b:a', '192k', # Audio bitrate
        '-shortest', # Output duration is shortest of inputs
        '-af', f"volume={audio_volume_db}dB", # Apply volume filter
        output_path
    ]
    stdout, stderr, returncode = run_shell_command(cmd, check_error=False, timeout=180)

    if returncode != 0:
        logger.error(f"FFmpeg failed to add audio: {stderr}")
        return None

    logger.info(f"Audio added to video. Output: {output_path}.")
    return output_path


def add_subtitles_to_video(
    video_path: str,
    subtitle_file_path: str,
    output_path: str,
    font_path: str,
    font_size: int,
    font_color: str,
    outline_color: str,
    outline_width: int,
    position: int # 1-9 for ASS positioning
) -> bool:
    """
    Adds burnt-in subtitles to a video using FFmpeg and a .ass subtitle file.
    """
    logger.info(f"Adding subtitles from {subtitle_file_path} to {video_path}...")
    if not os.path.exists(video_path):
        logger.error(f"Video file not found for subtitle addition: {video_path}")
        return False
    if not os.path.exists(subtitle_file_path):
        logger.error(f"Subtitle file not found: {subtitle_file_path}")
        return False
    if not os.path.exists(font_path):
        logger.warning(f"Font file not found at {font_path}. Subtitles may not render correctly. Falling back to system font.")
        # Attempt to proceed but warn
        font_path = "Arial" # Fallback to a common system font name if path not found

    # FFmpeg requires font path to be absolute and potentially quoted
    escaped_subtitle_file_path = subtitle_file_path.replace('\\', '/') # FFmpeg prefers forward slashes
    
    # The subtitles filter does not directly take font_size, color, outline_color, outline_width, position
    # as direct arguments. These are handled by the ASS file itself.
    # The `font_path` is crucial for FFmpeg to find the specific font.
    # We'll pass `fontsdir` to help FFmpeg locate the font.
    fonts_dir = os.path.dirname(font_path) if os.path.exists(font_path) else "/usr/share/fonts/truetype/dejavu" # Common fallback
    
    cmd = [
        'ffmpeg', '-y',
        '-i', shlex.quote(video_path),
        '-vf', f"subtitles={shlex.quote(escaped_subtitle_file_path)}:fontsdir={shlex.quote(fonts_dir)}",
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
    Note: This is for drawtext, not typically needed for ASS subtitles as ASS handles its own escaping.
    Updated to handle newlines correctly.
    """
    # Escape existing backslashes first to avoid double-escaping issues later
    text = text.replace('\\', '\\\\')
    # Escape single quotes, as they often delimit strings in filter options
    text = text.replace("'", "\\'")
    # Escape colons, crucial for filter options where : is a separator
    text = text.replace(':', '\\:')
    # Escape newlines, turning them into FFmpeg's internal newline representation
    text = text.replace('\n', '\\n')
    return text
