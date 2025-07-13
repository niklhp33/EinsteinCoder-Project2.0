import logging
import os
import requests
import json
import random
import shutil
import shlex
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse, parse_qs
import uuid
import time # For retries

from config import GLOBAL_CONFIG
from utils.shell_utils import run_shell_command
from utils.audio_utils import get_audio_duration_ffprobe # Absolute import
from utils.cleanup import RUNTIME_BASE_DIR # Import RUNTIME_BASE_DIR for absolute pathing

logger = logging.getLogger(__name__)

def get_video_duration(video_path: str) -> Optional[float]:
    """
    Gets the duration of a video file using ffprobe.
    """
    if not os.path.exists(video_path):
        logger.warning(f"Video file not found for duration check: {video_path}")
        return None
    
    cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', shlex.quote(video_path)]
    stdout, stderr, returncode = run_shell_command(cmd, check_error=False)
    
    if returncode != 0:
        logger.warning(f"ffprobe failed to get video duration for {video_path}: {stderr}")
        return None
    
    try:
        duration = float(stdout.strip())
        return duration
    except ValueError:
        logger.warning(f"Could not parse duration from ffprobe output for {video_path}: {stdout}")
        return None

def inject_silent_audio_if_needed(video_path: str, output_path: str, video_duration: float) -> Optional[str]:
    """
    Checks if a video has an audio track. If not, it injects a silent audio track
    of the same duration as the video. This is crucial for MoviePy compatibility.
    """
    logger.info(f"Checking audio track for {video_path} (duration: {video_duration:.2f}s).")
    
    cmd_check_audio = ['ffprobe', '-v', 'error', '-select_streams', 'a:0', '-show_entries', 'stream=codec_name', '-of', 'default=noprint_wrappers=1:nokey=1', shlex.quote(video_path)]
    stdout, stderr, returncode = run_shell_command(cmd_check_audio, check_error=False)

    if returncode == 0 and stdout.strip():
        logger.info(f"Video {video_path} already has an audio track ({stdout.strip()}). No injection needed.")
        return video_path
    elif returncode == 1 and "No such stream" in stderr:
        logger.info(f"Video {video_path} has no audio track. Injecting silent audio.")
    else:
        logger.warning(f"Could not confidently determine audio presence for {video_path}. Proceeding with silent audio injection just in case. ffprobe output: {stdout}, {stderr}")
        
    # CORRECTED: Construct silent_audio_path using the absolute RUNTIME_BASE_DIR
    temp_files_dir_abs = os.path.join(RUNTIME_BASE_DIR, GLOBAL_CONFIG['paths']['temp_files_dir'])
    os.makedirs(temp_files_dir_abs, exist_ok=True) # Ensure the directory exists
    silent_audio_path = os.path.join(temp_files_dir_abs, f"silent_audio_{uuid.uuid4().hex}.mp3")
    
    cmd_generate_silent = [
        'ffmpeg', '-y',
        '-f', 'lavfi',
        '-i', 'anullsrc=r=48000:cl=stereo,aresample=48000',
        '-t', str(video_duration),
        '-acodec', 'libmp3lame',
        shlex.quote(silent_audio_path)
    ]
    stdout, stderr, returncode = run_shell_command(cmd_generate_silent, check_error=True, timeout=60)
    
    if returncode != 0:
        logger.error(f"Failed to generate silent audio for {video_path}: {stderr}")
        return None
    
    cmd_mux = [
        'ffmpeg', '-y',
        '-i', shlex.quote(video_path),
        '-i', shlex.quote(silent_audio_path),
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-shortest',
        shlex.quote(output_path)
    ]
    stdout, stderr, returncode = run_shell_command(cmd_mux, check_error=True, timeout=120)

    if os.path.exists(silent_audio_path):
        os.remove(silent_audio_path)

    if returncode != 0:
        logger.error(f"Failed to inject silent audio into {video_path}: {stderr}")
        return None
    
    logger.info(f"Injected silent audio for clip {video_path} into {output_path}.")
    return output_path

def search_pexels_videos(query: str, orientation: str = 'portrait', per_page: int = 15, min_duration_s: int = 5, max_duration_s: int = 30) -> List[Dict[str, Any]]:
    """
    Searches Pexels for free stock videos.
    """
    api_key = GLOBAL_CONFIG['api_keys']['pexels_api_key']
    if not api_key or api_key == 'YOUR_PEXELS_API_KEY_PLACEHOLDER':
        logger.error("Pexels API key not configured. Cannot search Pexels videos.")
        return []

    url = "https://api.pexels.com/videos/search"
    headers = {"Authorization": api_key}
    params = {
        "query": query,
        "orientation": orientation,
        "per_page": per_page,
        "min_duration": min_duration_s,
        "max_duration": max_duration_s
    }

    logger.info(f"Searching Pexels for '{query}' (orientation: {orientation})...")
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        videos_info = []
        if 'videos' in data:
            for video in data['videos']:
                best_file = None
                for file in video['video_files']:
                    if file['file_type'] == 'video/mp4' and 'link' in file:
                        if best_file is None or file['width'] * file['height'] > best_file['width'] * best_file['height']:
                            best_file = file
                
                if best_file:
                    videos_info.append({
                        'id': video['id'],
                        'duration': video['duration'],
                        'width': video['width'],
                        'height': video['height'],
                        'url': video['url'],
                        'download_link': best_file['link']
                    })
        logger.info(f"Found {len(videos_info)} videos from Pexels for '{query}'.")
        return videos_info
    except requests.exceptions.RequestException as e:
        logger.error(f"Error searching Pexels videos for '{query}': {e}")
        return []

def search_pixabay_videos(query: str, orientation: str = 'vertical', per_page: int = 15, min_duration_s: int = 5, max_duration_s: int = 30) -> List[Dict[str, Any]]:
    """
    Searches Pixabay for free stock videos.
    """
    api_key = GLOBAL_CONFIG['api_keys']['pixabay_api_key']
    if not api_key or api_key == 'YOUR_PIXABAY_API_KEY_PLACEHOLDER':
        logger.error("Pixabay API key not configured. Cannot search Pixabay videos.")
        return []

    url = "https://pixabay.com/api/videos/"
    params = {
        "key": api_key,
        "q": query,
        "orientation": orientation,
        "per_page": per_page,
        "min_duration": min_duration_s,
        "max_duration": max_duration_s
    }

    logger.info(f"Searching Pixabay for '{query}' (orientation: {orientation})...")
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        videos_info = []
        if 'hits' in data:
            for hit in data['hits']:
                best_quality_url = None
                if 'videos' in hit:
                    if 'large' in hit['videos'] and 'url' in hit['videos']['large']:
                        best_quality_url = hit['videos']['large']['url']
                    elif 'medium' in hit['videos'] and 'url' in hit['videos']['medium']:
                        best_quality_url = hit['videos']['medium']['url']
                    elif 'small' in hit['videos'] and 'url' in hit['videos']['small']:
                        best_quality_url = hit['videos']['small']['url']
                
                if best_quality_url:
                    videos_info.append({
                        'id': hit['id'],
                        'duration': hit['duration'],
                        'width': hit['videos']['large']['width'] if 'large' in hit['videos'] else hit['videos']['medium']['width'],
                        'height': hit['videos']['large']['height'] if 'large' in hit['videos'] else hit['videos']['medium']['height'],
                        'url': hit['pageURL'],
                        'download_link': best_quality_url
                    })
        logger.info(f"Found {len(videos_info)} videos from Pixabay for '{query}'.")
        return videos_info
    except requests.exceptions.RequestException as e:
        logger.error(f"Error searching Pixabay videos for '{query}': {e}")
        return []

def download_video_clip(video_url: str, download_dir: str, prefix: str = "downloaded_clip") -> Optional[str]:
    """
    Downloads a video clip from a given URL to a specified directory.
    """
    if not video_url:
        logger.error("No video URL provided for download.")
        return None

    file_extension = 'mp4' 
    filename = f"{prefix}_{uuid.uuid4().hex}.{file_extension}"
    filepath = os.path.join(download_dir, filename)

    logger.info(f"Downloading video from {video_url} to {filepath}")
    try:
        with requests.get(video_url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(filepath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        logger.info(f"Successfully downloaded: {filepath}")
        return filepath
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading video from {video_url}: {e}")
        if os.path.exists(filepath):
            os.remove(filepath)
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred during download of {video_url}: {e}")
        if os.path.exists(filepath):
            os.remove(filepath)
        return None

def find_font_path(font_name: str) -> Optional[str]:
    """
    Attempts to find the absolute path of a font file based on its common name.
    Prioritizes .ttf, then .otf.
    Searches common Linux font directories first.
    """
    logger.info(f"Attempting to find font path for: {font_name}")
    # Common Linux font directories in Colab
    common_paths = [
        '/usr/share/fonts/truetype/liberation/',
        '/usr/share/fonts/truetype/dejavu/',
        '/usr/share/fonts/truetype/noto/',
        '/usr/share/fonts/truetype/ubuntu/',
        '/usr/local/share/fonts/',
        '/usr/share/fonts/'
    ]

    # Handle common font names or variations
    font_name_lower = font_name.lower().replace(" ", "")
    
    # Specific mapping for common fonts (case-insensitive and without spaces)
    font_mappings = {
        'roboto': 'Roboto-Regular.ttf',
        'arial': 'Arial.ttf',
        'verdana': 'Verdana.ttf',
        'timesnewroman': 'Times New Roman.ttf',
        'impact': 'Impact.ttf',
        'comicsansms': 'Comic Sans MS.ttf',
        'montserrat': 'Montserrat-Regular.ttf',
        'opensans': 'OpenSans-Regular.ttf',
        'lato': 'Lato-Regular.ttf',
        'oswald': 'Oswald-Regular.ttf',
        'poppins': 'Poppins-Regular.ttf',
        'sourcesanspro': 'SourceSansPro-Regular.ttf',
        'anton': 'Anton-Regular.ttf',
        'bashkir': 'Bashkir.ttf'
    }

    # Try exact mapping first
    if font_name_lower in font_mappings:
        specific_filename = font_mappings[font_name_lower]
        for path_dir in common_paths:
            full_path = os.path.join(path_dir, specific_filename)
            if os.path.exists(full_path):
                logger.info(f"Found font '{font_name}' at: {full_path}")
                return full_path
    
    # Fallback: Search all files in common directories
    for path_dir in common_paths:
        for root, _, files in os.walk(path_dir):
            for file in files:
                if font_name_lower in file.lower() and (file.endswith('.ttf') or file.endswith('.otf')):
                    full_path = os.path.join(root, file)
                    logger.info(f"Found font '{font_name}' (fallback search) at: {full_path}")
                    return full_path
    
    logger.warning(f"Font '{font_name}' not found in common system paths. Subtitles might default to a generic font.")
    return None
