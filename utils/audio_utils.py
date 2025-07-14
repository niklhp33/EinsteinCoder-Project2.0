import logging
import os
import shlex
import requests
import uuid
import time
from typing import List, Tuple, Optional, Any

from utils.shell_utils import run_shell_command
from config import GLOBAL_CONFIG # For API keys if needed for background music search

logger = logging.getLogger(__name__)

def get_audio_duration_ffprobe(audio_path: str) -> Optional[float]:
    """
    Gets the duration of an audio file using ffprobe.
    """
    if not os.path.exists(audio_path):
        logger.warning(f"Audio file not found for duration check: {audio_path}")
        return None

    cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', shlex.quote(audio_path)]
    stdout, stderr, returncode = run_shell_command(cmd, check_error=False)

    if returncode != 0:
        logger.warning(f"ffprobe failed to get audio duration for {audio_path}: {stderr}")
        return None

    try:
        duration = float(stdout.strip())
        return duration
    except ValueError:
        logger.warning(f"Could not parse duration from ffprobe output for {audio_path}: {stdout}")
        return None

def combine_audio_tracks(
    track1_path: str,
    track2_path: str,
    output_path: str,
    track1_volume_db: float = 0.0,
    track2_volume_db: float = -15.0 # Default for background music
) -> Optional[str]:
    """
    Combines two audio tracks into a single output file, adjusting their volumes.
    The output duration will be the length of the longest input track.
    """
    logger.info(f"Combining audio tracks: {track1_path} (vol: {track1_volume_db}dB) and {track2_path} (vol: {track2_volume_db}dB).")
    if not os.path.exists(track1_path):
        logger.error(f"Audio track 1 not found: {track1_path}")
        return None
    if not os.path.exists(track2_path):
        logger.error(f"Audio track 2 not found: {track2_path}")
        return None

    # Use amix filter for combining and volume adjustment
    # [0:a]volume=...[a1]; [1:a]volume=...[a2]; [a1][a2]amix=inputs=2:duration=longest
    filter_complex = f"[0:a]volume={track1_volume_db}dB[a1]; [1:a]volume={track2_volume_db}dB[a2]; [a1][a2]amix=inputs=2:duration=longest[aout]"

    cmd = [
        'ffmpeg', '-y',
        '-i', shlex.quote(track1_path),
        '-i', shlex.quote(track2_path),
        '-filter_complex', filter_complex,
        '-map', '[aout]',
        '-c:a', 'aac',
        '-b:a', '192k',
        output_path
    ]
    stdout, stderr, returncode = run_shell_command(cmd, check_error=False, timeout=120)

    if returncode != 0:
        logger.error(f"FFmpeg failed to combine audio tracks: {stderr}")
        return None

    logger.info(f"Audio tracks combined. Output: {output_path}.")
    return output_path

def download_background_music(query: str, output_dir: str, max_retries: int = 3, delay_s: int = 5) -> Optional[str]:
    """
    Simulates downloading background music based on a query.
    In a real scenario, this would integrate with a royalty-free music API (e.g., Pixabay, Pexels, or a dedicated music library).
    For now, it creates a dummy audio file.
    """
    logger.info(f"Simulating download of background music for query: '{query}'")
    os.makedirs(output_dir, exist_ok=True)
    output_filepath = os.path.join(output_dir, f"background_music_{uuid.uuid4().hex}.mp3")

    # Create a dummy MP3 file (very small, silent)
    # This is a minimal valid MP3 header for a silent 1-second file.
