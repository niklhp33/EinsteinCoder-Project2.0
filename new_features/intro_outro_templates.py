import logging
import os
import shutil
from typing import Optional, List

logger = logging.getLogger(__name__)

# Dummy paths for template assets (in a real project, these would be managed)
_DUMMY_TEMPLATE_DIR = "/tmp/tiktok_project_runtime/templates"
_DUMMY_INTRO_VIDEO = os.path.join(_DUMMY_TEMPLATE_DIR, "intro_template.mp4")
_DUMMY_OUTRO_VIDEO = os.path.join(_DUMMY_TEMPLATE_DIR, "outro_template.mp4")

def _create_dummy_template_files():
    """Creates dummy video files for testing templates."""
    os.makedirs(_DUMMY_TEMPLATE_DIR, exist_ok=True)
    from utils.shell_utils import run_shell_command
    from utils.video_utils import get_video_duration # Use local alias to prevent collision

    if not os.path.exists(_DUMMY_INTRO_VIDEO):
        logger.info(f"Creating dummy intro video: {_DUMMY_INTRO_VIDEO}")
        cmd_intro = ['ffmpeg', '-y', '-f', 'lavfi', '-i', 'color=c=blue:s=1280x720:d=3,format=yuv420p', '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '30', _DUMMY_INTRO_VIDEO]
        run_shell_command(cmd_intro, check_error=False, timeout=10)
    
    if not os.path.exists(_DUMMY_OUTRO_VIDEO):
        logger.info(f"Creating dummy outro video: {_DUMMY_OUTRO_VIDEO}")
        cmd_outro = ['ffmpeg', '-y', '-f', 'lavfi', '-i', 'color=c=red:s=1280x720:d=3,format=yuv420p', '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '30', _DUMMY_OUTRO_VIDEO]
        run_shell_command(cmd_outro, check_error=False, timeout=10)


def get_available_intro_templates() -> List[str]:
    """
    Retrieves a list of available intro video templates.
    This is a placeholder; in a real system, it would query a template database or storage.
    """
    _create_dummy_template_files() # Ensure dummy files exist for demonstration
    logger.info("Retrieving available intro templates.")
    return ["Standard Intro", "Dynamic Title Intro"] if os.path.exists(_DUMMY_INTRO_VIDEO) else []

def get_available_outro_templates() -> List[str]:
    """
    Retrieves a list of available outro video templates.
    """
    _create_dummy_template_files() # Ensure dummy files exist for demonstration
    logger.info("Retrieving available outro templates.")
    return ["Standard Outro", "Social Media CTA Outro"] if os.path.exists(_DUMMY_OUTRO_VIDEO) else []

def apply_intro_template(main_video_path: str, intro_template_name: str, output_path: str) -> Optional[str]:
    """
    Applies an intro template to the beginning of the main video.
    This is a conceptual placeholder using simple FFmpeg concatenation.
    """
    logger.info(f"Applying intro template '{intro_template_name}' to {main_video_path}...")
    _create_dummy_template_files() # Ensure dummy files exist
    
    if not os.path.exists(main_video_path):
        logger.error(f"Main video not found for intro application: {main_video_path}")
        return None

    intro_video_path = _DUMMY_INTRO_VIDEO # Use the dummy intro for now

    if not os.path.exists(intro_video_path):
        logger.error(f"Intro template video not found at expected path: {intro_video_path}")
        return None
    
    from utils.ffmpeg_utils import concatenate_videos
    
    # Simple concatenation (no complex transitions here for template joining)
    # Get properties of the main video to ensure consistency
    from utils.video_utils import get_video_resolution
    width, height = get_video_resolution(main_video_path)
    if not width or not height:
        logger.warning(f"Could not get resolution of main video {main_video_path}. Using default 1080x1920 for concat.")
        width, height = 1080, 1920 # Fallback

    concatenated_path = concatenate_videos(
        video_paths=[intro_video_path, main_video_path],
        output_path=output_path,
        target_width=width,
        target_height=height,
        target_duration=(get_video_duration(intro_video_path) or 0) + (get_video_duration(main_video_path) or 0),
        transition="none" # Typically no transition for intro/main video join
    )
    
    if not concatenated_path:
        logger.error("Failed to apply intro template via concatenation.")
        return None

    logger.info(f"Intro template applied. Output: {concatenated_path}")
    return concatenated_path

def apply_outro_template(main_video_path: str, outro_template_name: str, output_path: str) -> Optional[str]:
    """
    Applies an outro template to the end of the main video.
    This is a conceptual placeholder using simple FFmpeg concatenation.
    """
    logger.info(f"Applying outro template '{outro_template_name}' to {main_video_path}...")
    _create_dummy_template_files() # Ensure dummy files exist

    if not os.path.exists(main_video_path):
        logger.error(f"Main video not found for outro application: {main_video_path}")
        return None

    outro_video_path = _DUMMY_OUTRO_VIDEO # Use the dummy outro for now

    if not os.path.exists(outro_video_path):
        logger.error(f"Outro template video not found at expected path: {outro_video_path}")
        return None

    from utils.ffmpeg_utils import concatenate_videos
    from utils.video_utils import get_video_resolution
    
    width, height = get_video_resolution(main_video_path)
    if not width or not height:
        logger.warning(f"Could not get resolution of main video {main_video_path}. Using default 1080x1920 for concat.")
        width, height = 1080, 1920 # Fallback

    concatenated_path = concatenate_videos(
        video_paths=[main_video_path, outro_video_path],
        output_path=output_path,
        target_width=width,
        target_height=height,
        target_duration=(get_video_duration(main_video_path) or 0) + (get_video_duration(outro_video_path) or 0),
        transition="none" # Typically no transition for main video/outro join
    )

    if not concatenated_path:
        logger.error("Failed to apply outro template via concatenation.")
        return None

    logger.info(f"Outro template applied. Output: {concatenated_path}")
    return concatenated_path
