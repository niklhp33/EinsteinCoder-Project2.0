import os
import sys

# Assume PROJECT_ROOT_DIR is already added to sys.path from the main notebook setup
# If running this script standalone, PROJECT_ROOT_DIR needs to be defined
if 'PROJECT_ROOT_DIR' not in globals():
    PROJECT_ROOT_DIR = '/content/drive/MyDrive/project_2.0' # Fallback for standalone execution

def generate_writefile_list_to_drive():
    """
    Generates a list of all project Python files (written by %%writefile)
    and saves it to a text file in the project's docs folder on Google Drive.
    """
    project_files = [
        "config.py",
        "models.py",
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
        "pipeline.py",
        "ui_pipeline.py",
        os.path.join("new_features", "project_roadmap.py"), # Include the roadmap itself
        # Add other new_features placeholder files if you want them listed here
        os.path.join("new_features", "advanced_tts_controls.py"),
        os.path.join("new_features", "cost_analyzer.py"),
        os.path.join("new_features", "dynamic_visual_cues.py"),
        os.path.join("new_features", "interactive_content_generation.py"),
        os.path.join("new_features", "intro_outro_templates.py"),
        os.path.join("new_features", "long_form_adaptation.py"),
        os.path.join("new_features", "niche_content_specialization.py"),
        os.path.join("new_features", "integrated_music_library.py"),
        os.path.join("new_features", "multilingual_support.py"),
    ]

    output_list = []
    output_list.append("--- Einstein Coder Project Files (written by %%writefile) ---\n")
    output_list.append("These are the relative paths from your project_2.0 folder:\n")

    for i, file_path_rel in enumerate(project_files):
        full_path_on_drive = os.path.join(PROJECT_ROOT_DIR, file_path_rel)
        status = " (Exists)" if os.path.exists(full_path_on_drive) else " (MISSING!)"
        output_list.append(f"{i+1}. {file_path_rel}{status}\n")
    
    output_list.append("\n--- END OF LIST ---")

    docs_dir = os.path.join(PROJECT_ROOT_DIR, 'docs')
    os.makedirs(docs_dir, exist_ok=True) # Ensure docs dir exists
    
    output_filename = os.path.join(docs_dir, "writefile_cells_list.txt")
    
    with open(output_filename, 'w') as f:
        f.writelines(output_list)
    
    print(f"\nList of %%writefile cells generated and saved to Google Drive: {output_filename}")
    print("Please check this file in your project_2.0/docs folder.")

if __name__ == "__main__":
    generate_writefile_list_to_drive()
