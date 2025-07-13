# __init__.py for the utils package
# This file exports common utility functions from its submodules for easier access.

# Import specific functions/constants from submodules using their updated names
from utils.shell_utils import run_shell_command
from utils.gcs_utils import get_gcs_client, upload_to_gcs, download_from_gcs, list_blobs, delete_blob
from utils.cleanup import setup_runtime_directories, cleanup_runtime_files, VIDEO_DOWNLOADS_DIR, AUDIO_DIR, IMAGES_DIR, OUTPUT_DIR, TEMP_FILES_DIR, LOGS_DIR, RUNTIME_BASE_DIR
from utils.ffmpeg_utils import get_video_dimensions, concatenate_videos, add_audio_to_video, add_subtitles_to_video, escape_ffmpeg_text
from utils.video_utils import search_pexels_videos, search_pixabay_videos, download_video_clip, inject_silent_audio_if_needed, get_video_duration, find_font_path
from utils.audio_utils import get_audio_duration_ffprobe, adjust_audio_volume, combine_audio_tracks, synthesize_speech_google, synthesize_speech_azure, synthesize_speech_gtts


# Define __all__ to control what's imported when doing 'from utils import *'
__all__ = [
    "run_shell_command",
    "get_gcs_client", "upload_to_gcs", "download_from_gcs", "list_blobs", "delete_blob",
    "setup_runtime_directories", "cleanup_runtime_files", 
    "VIDEO_DOWNLOADS_DIR", "AUDIO_DIR", "IMAGES_DIR", "OUTPUT_DIR", "TEMP_FILES_DIR", "LOGS_DIR", "RUNTIME_BASE_DIR",
    "get_video_dimensions", "concatenate_videos", "add_audio_to_video", "add_subtitles_to_video", "escape_ffmpeg_text",
    "search_pexels_videos", "search_pixabay_videos", "download_video_clip", "inject_silent_audio_if_needed", "get_video_duration", "find_font_path",
    "get_audio_duration_ffprobe", "adjust_audio_volume", "combine_audio_tracks", "synthesize_speech_google", "synthesize_speech_azure", "synthesize_speech_gtts"
]
