import os
import logging
import datetime
from typing import List # Added for comprehensive type hinting

logger = logging.getLogger(__name__)

def update_project_file_list(project_root_dir: str): # <-- CRITICAL FIX: Ensure this signature is correct
    """
    Generates an updated list of all project Python files (*.py) expected in
    the project_2.0 structure and saves it to a text file on Google Drive.
    This function can be called whenever the project structure is updated.
    """
    project_files_expected = [
        "config.py",
        "models.py",
        "pipeline.py",
        "ui_pipeline.py",
        "write_all_project_files.py", # The script that could write all others (if used)
        os.path.join("utils", "__init__.py"),
        os.path.join("utils", "shell_utils.py"),
        os.path.join("utils", "gcs_utils.py"),
        os.path.join("utils", "cleanup.py"),
        os.path.join("utils", "ffmpeg_utils.py"),
        os.path.join("utils", "audio_utils.py"),
        os.path.join("utils", "video_utils.py"),
        os.path.join("ai_integration", "__init__.py"),
        os.path.join("ai_integration", "gemini_integration.py"),
        os.path.join("ai_integration", "speech_synthesis.py"),
        os.path.join("ai_integration", "image_video_generation.py"),
        os.path.join("media_processing", "__init__.py"),
        os.path.join("media_processing", "video_editor.py"),
        os.path.join("new_features", "__init__.py"),
        os.path.join("new_features", "project_roadmap.py"),
        os.path.join("new_features", "advanced_tts_controls.py"),
        os.path.join("new_features", "cost_analyzer.py"),
        os.path.join("new_features", "dynamic_visual_cues.py"),
        os.path.join("new_features", "interactive_content_generation.py"),
        os.path.join("new_features", "intro_outro_templates.py"),
        os.path.join("new_features", "long_form_adaptation.py"),
        os.path.join("new_features", "niche_content_specialization.py"),
        os.path.join("new_features", "integrated_music_library.py"),
        os.path.join("new_features", "multilingual_support.py"),
        os.path.join("new_features", "feature_integration_pipeline.py"),
        os.path.join("new_features", "list_writefiles.py"),
    ]

    output_lines = []
    output_lines.append("--- Einstein Coder Project Files List ---\n")
    output_lines.append("Generated on: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n")
    output_lines.append("Relative paths from project_2.0 folder, with existence check:\n\n")

    docs_dir = os.path.join(project_root_dir, 'docs')
    os.makedirs(docs_dir, exist_ok=True)

    output_filename = os.path.join(docs_dir, "project_files_list.txt")

    for i, file_path_rel in enumerate(project_files_expected):
        full_path_on_drive = os.path.join(project_root_dir, file_path_rel)
        status = " (Exists)" if os.path.exists(full_path_on_drive) else " (MISSING!)"
        output_lines.append(f"{i+1:02d}. {file_path_rel}{status}\n")

    output_lines.append("\n--- END OF LIST ---\n") # Ensured final newline to prevent unterminated string issues

    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.writelines(output_lines)
        logger.info(f"Project file list generated and saved to Google Drive: {output_filename}")
    except Exception as e:
        logger.error(f"Failed to write project file list to Drive: {e}", exc_info=True)

if __name__ == "__main__":
    if 'PROJECT_ROOT_DIR' in globals():
        update_project_file_list(globals()['PROJECT_ROOT_DIR'])
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        logger.warning("PROJECT_ROOT_DIR not found. Attempting with current directory (may not be correct in Colab).")
        update_project_file_list(os.getcwd())
