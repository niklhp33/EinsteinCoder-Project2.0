import logging
import os
import shlex
import subprocess
from typing import Optional, Tuple, List

from utils.shell_utils import run_shell_command

logger = logging.getLogger(__name__)

def get_video_duration(video_path: str) -> Optional[float]:
    """
    Gets the duration of a video file in seconds using ffprobe.
    Returns None if the duration cannot be determined.
    """
    if not os.path.exists(video_path):
        logger.warning(f"Video file not found for duration check: {video_path}")
        return None

    cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', shlex.quote(video_path)]
    stdout, stderr, returncode = run_shell_command(cmd, check_error=False)

    if returncode != 0:
        logger.warning(f"ffprobe failed to get duration for {video_path}: {stderr}")
        return None

    try:
        duration = float(stdout.strip())
        return duration
    except ValueError:
        logger.warning(f"Could not parse duration from ffprobe output for {video_path}: {stdout}")
        return None

def get_video_resolution(video_path: str) -> Optional[Tuple[int, int]]:
    """
    Gets the resolution (width, height) of a video file using ffprobe.
    Returns None if the resolution cannot be determined.
    """
    if not os.path.exists(video_path):
        logger.warning(f"Video file not found for resolution check: {video_path}")
        return None

    cmd = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height',
           '-of', 'csv=p=0:s=x', shlex.quote(video_path)]
    stdout, stderr, returncode = run_shell_command(cmd, check_error=False)

    if returncode != 0:
        logger.warning(f"ffprobe failed to get resolution for {video_path}: {stderr}")
        return None

    try:
        width, height = map(int, stdout.strip().split('x'))
        return width, height
    except ValueError:
        logger.warning(f"Could not parse resolution from ffprobe output for {video_path}: {stdout}")
        return None

def download_video_clip(video_url: str, output_path: str) -> Optional[str]:
    """
    Simulates downloading a video clip from a URL.
    In a real scenario, this would use a robust downloader (e.g., requests, youtube-dl).
    For now, it creates a dummy video file.
    """
    logger.info(f"Simulating downloading video clip from {video_url} to {output_path}")
    
    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Create a small dummy MP4 file (minimal valid MP4)
    # This is a highly simplified dummy. A proper dummy would need proper headers.
    # For a truly 'playable' dummy, you'd generate a small blank video with ffmpeg:
    # ffmpeg -y -f lavfi -i color=c=black:s=1280x720:d=1 -pix_fmt yuv420p dummy.mp4
    try:
        # Create a dummy file that ffmpeg might accept as input
        # This one creates a 1-second black video 640x360
        dummy_cmd = [
            'ffmpeg', '-y',
            '-f', 'lavfi', '-i', 'color=c=black:s=640x360:d=1',
            '-vf', 'format=yuv420p', # Ensure pixel format is compatible
            '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '30',
            shlex.quote(output_path)
        ]
        stdout, stderr, returncode = run_shell_command(dummy_cmd, check_error=False, timeout=10)
        if returncode != 0:
            logger.warning(f"Failed to create dummy video, creating empty file instead: {stderr}")
            with open(output_path, 'wb') as f:
                f.write(b'DUMMY VIDEO CONTENT') # fallback to empty if ffmpeg fails
    except Exception as e:
        logger.warning(f"Exception creating dummy video: {e}, creating empty file instead.")
        with open(output_path, 'wb') as f:
            f.write(b'DUMMY VIDEO CONTENT') # fallback to empty if ffmpeg fails

    if os.path.exists(output_path):
        logger.info(f"Simulated video download complete. Dummy file created at: {output_path}")
        return output_path
    else:
        logger.error(f"Failed to create dummy video file at {output_path}")
        return None

def search_pexels_videos(query: str, api_key: str, orientation: str = 'portrait', per_page: int = 10) -> List[Dict[str, Any]]:
    """
    Searches for videos on Pexels. This is a functional placeholder.
    In a real implementation, it would make an API call to Pexels.
    """
    logger.info(f"Simulating Pexels video search for '{query}', orientation: '{orientation}'")
    # Real Pexels API endpoint: https://api.pexels.com/videos/search
    # headers = {"Authorization": api_key}
    # params = {"query": query, "orientation": orientation, "per_page": per_page}
    # response = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params)
    # data = response.json()
    # return data.get('videos', [])

    # Placeholder for Pexels search results
    dummy_videos = []
    for i in range(min(per_page, 3)): # Return a few dummy results
        dummy_videos.append({
            "id": f"pexels_dummy_{i}",
            "url": f"https://www.pexels.com/video/dummy-video-{i}/",
            "image": "https://images.pexels.com/videos/pixels-dummy.jpeg",
            "duration": 15 + i*5, # Dummy duration
            "video_files": [
                {"link": f"http://example.com/dummy_pexels_video_{i}.mp4", "quality": "hd", "width": 1080, "height": 1920, "fps": 30},
                {"link": f"http://example.com/dummy_pexels_video_sd_{i}.mp4", "quality": "sd", "width": 720, "height": 1280, "fps": 30}
            ]
        })
    logger.info(f"Simulated Pexels search returned {len(dummy_videos)} results.")
    return dummy_videos

def search_pixabay_videos(query: str, api_key: str, editors_choice: bool = True, per_page: int = 10) -> List[Dict[str, Any]]:
    """
    Searches for videos on Pixabay. This is a functional placeholder.
    In a real implementation, it would make an API call to Pixabay.
    """
    logger.info(f"Simulating Pixabay video search for '{query}', editors_choice: {editors_choice}")
    # Real Pixabay API endpoint: https://pixabay.com/api/videos/
    # params = {"key": api_key, "q": query, "editors_choice": "true" if editors_choice else "false", "per_page": per_page}
    # response = requests.get("https://pixabay.com/api/videos/", params=params)
    # data = response.json()
    # return data.get('hits', [])

    # Placeholder for Pixabay search results
    dummy_videos = []
    for i in range(min(per_page, 3)): # Return a few dummy results
        dummy_videos.append({
            "id": f"pixabay_dummy_{i}",
            "pageURL": f"https://pixabay.com/videos/dummy-video-{i}/",
            "picture_id": f"dummy_{i}",
            "duration": 20 + i*3, # Dummy duration
            "videos": {
                "tiny": {"url": f"http://example.com/dummy_pixabay_tiny_video_{i}.mp4"},
                "small": {"url": f"http://example.com/dummy_pixabay_small_video_{i}.mp4"},
                "medium": {"url": f"http://example.com/dummy_pixabay_medium_video_{i}.mp4"},
                "large": {"url": f"http://example.com/dummy_pixabay_large_video_{i}.mp4"}
            }
        })
    logger.info(f"Simulated Pixabay search returned {len(dummy_videos)} results.")
    return dummy_videos
