import os
import shutil
import logging
from config import GLOBAL_CONFIG

logger = logging.getLogger(__name__)

# Define paths relative to the base_dir in config.py
RUNTIME_BASE_DIR = GLOBAL_CONFIG['paths']['base_dir']
VIDEO_DOWNLOADS_DIR = os.path.join(RUNTIME_BASE_DIR, GLOBAL_CONFIG['paths']['video_downloads_dir'])
AUDIO_DIR = os.path.join(RUNTIME_BASE_DIR, GLOBAL_CONFIG['paths']['audio_dir'])
IMAGES_DIR = os.path.join(RUNTIME_BASE_DIR, GLOBAL_CONFIG['paths']['images_dir'])
OUTPUT_DIR = os.path.join(RUNTIME_BASE_DIR, GLOBAL_CONFIG['paths']['output_dir'])
TEMP_FILES_DIR = os.path.join(RUNTIME_BASE_DIR, GLOBAL_CONFIG['paths']['temp_files_dir'])
LOGS_DIR = os.path.join(RUNTIME_BASE_DIR, GLOBAL_CONFIG['paths']['logs_dir'])

def setup_runtime_directories():
    """
    Ensures all necessary local runtime directories exist.
    This function creates the /tmp/tiktok_project_runtime and its subfolders.
    """
    os.makedirs(RUNTIME_BASE_DIR, exist_ok=True)
    os.makedirs(VIDEO_DOWNLOADS_DIR, exist_ok=True)
    os.makedirs(AUDIO_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(TEMP_FILES_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)
    logger.info(f"All runtime directories ensured under: {RUNTIME_BASE_DIR}")

def cleanup_runtime_files():
    """
    Cleans up all temporary files and directories created during the pipeline execution.
    This deletes the entire base runtime directory and its contents.
    """
    logger.info(f"Initiating cleanup of temporary runtime files under: {RUNTIME_BASE_DIR}")
    try:
        if os.path.exists(RUNTIME_BASE_DIR):
            # Iterate and remove contents, then remove the base directory itself
            for item in os.listdir(RUNTIME_BASE_DIR):
                item_path = os.path.join(RUNTIME_BASE_DIR, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                    logger.info(f"Cleaned up temporary directory: {item_path}")
                else:
                    os.remove(item_path)
                    logger.info(f"Cleaned up temporary file: {item_path}")

            # After removing all contents, remove the base directory
            if not os.listdir(RUNTIME_BASE_DIR): # Check if it's empty before removing
                os.rmdir(RUNTIME_BASE_DIR)
                logger.info(f"Removed empty base runtime directory: {RUNTIME_BASE_DIR}")
            else:
                logger.warning(f"Runtime base directory {RUNTIME_BASE_DIR} is not empty after cleanup attempt.")


        logger.info("Temporary file cleanup complete.")
    except Exception as e:
        logger.error(f"Error during temporary file cleanup: {e}", exc_info=True)
