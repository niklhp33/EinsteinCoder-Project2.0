import gradio as gr
import os
import sys
import logging
import time
from datetime import datetime
import json

# Ensure absolute imports
from config import GLOBAL_CONFIG
from models import (
    VideoParams, VideoLanguage, VideoAspect, VideoSourceType, VideoConcatMode,
    VideoTransitionMode, SpeechSynthesisVoice, SubtitleFont, SubtitlePosition
)
from pipeline import VideoGenerationPipeline

# --- Setup for logging and Project Root ---
# This part is redundant as main execution cell already sets up logging and PROJECT_ROOT_DIR
# However, keeping it for local testing capability if ui_pipeline.py is run directly.

# Determine PROJECT_ROOT_DIR for UI script context
PROJECT_ROOT_DIR_UI = os.path.dirname(os.path.abspath(__file__)) # This should be /content/drive/MyDrive/project_2.0
if not os.path.exists(os.path.join(PROJECT_ROOT_DIR_UI, 'config.py')):
    if '/content/drive/MyDrive/project_2.0' in sys.path:
        PROJECT_ROOT_DIR_UI = '/content/drive/MyDrive/project_2.0'
    else:
        PROJECT_ROOT_DIR_UI = '/project_2.0'
        logging.getLogger(__name__).warning(f"UI Script: PROJECT_ROOT_DIR not found, using fallback: {PROJECT_ROOT_DIR_UI}")

if PROJECT_ROOT_DIR_UI not in sys.path:
    sys.path.append(PROJECT_ROOT_DIR_UI)

if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)
logger.info("UI Script: Imported all necessary modules. Setting up UI.")

# --- Define the Gradio UI function ---
def generate_video_ui(
    video_subject: str,
    video_language: str,
    video_source_type: str,
    image_prompt_suffix: str,
    video_concat_mode: str,
    video_transition_mode: str,
    video_aspect_ratio: str,
    max_clip_duration_s: int,
    num_videos_to_source_or_generate: int,
    final_video_duration_s: int,
    speech_synthesis_voice: str,
    enable_subtitles: bool,
    subtitle_font: str,
    subtitle_position: str,
    subtitle_font_size: int,
    subtitle_color: str,
    subtitle_outline_color: str,
    subtitle_outline_width: int
):
    start_time = time.time()
    logger.info("--- Starting Video Generation Pipeline ---")
    
    try:
        params = VideoParams(
            video_subject=video_subject,
            video_language=VideoLanguage(video_language),
            video_source_type=VideoSourceType(video_source_type),
            image_prompt_suffix=image_prompt_suffix if image_prompt_suffix else None,
            video_concat_mode=VideoConcatMode(video_concat_mode),
            video_transition_mode=VideoTransitionMode(video_transition_mode),
            video_aspect_ratio=VideoAspect(video_aspect_ratio),
            max_clip_duration_s=max_clip_duration_s,
            num_videos_to_source_or_generate=num_videos_to_source_or_generate,
            final_video_duration_s=final_video_duration_s,
            speech_synthesis_voice=SpeechSynthesisVoice(speech_synthesis_voice),
            enable_subtitles=enable_subtitles,
            subtitle_font=SubtitleFont(subtitle_font),
            subtitle_position=SubtitlePosition(subtitle_position),
            subtitle_font_size=subtitle_font_size,
            subtitle_color=subtitle_color,
            subtitle_outline_color=subtitle_outline_color,
            subtitle_outline_width=subtitle_outline_width
        )
    except Exception as e:
        logger.error(f"Error parsing UI parameters: {e}")
        return "Video generation failed: Invalid UI parameters.", None, None

    logger.info(f"UI submitted parameters: {json.dumps(params.dict(), indent=2)}")

    output_video_path = None
    pipeline_log_path = None
    
    log_filename = f"pipeline_log_FULL_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    temp_log_filepath = os.path.join(GLOBAL_CONFIG['paths']['base_dir'], GLOBAL_CONFIG['paths']['logs_dir'], log_filename)
    
    pipeline_file_handler = None
    try:
        os.makedirs(os.path.dirname(temp_log_filepath), exist_ok=True)
        pipeline_file_handler = logging.FileHandler(temp_log_filepath)
        pipeline_file_handler.setLevel(logging.INFO)
        pipeline_file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(pipeline_file_handler)
        logger.info(f"Logging configured to console AND temporary file: {temp_log_filepath}")

        pipeline_instance = VideoGenerationPipeline()
        success = pipeline_instance.run(params=params)

        if success:
            status_message = "Video generation completed successfully! Check your Google Drive 'project_2.0/output' folder."
            guessed_output_filename = f"final_video_{params.video_subject.replace(' ', '_')}_"
            status_message += f"\n(Approximate filename: {guessed_output_filename}*.mp4)"
            
            log_filename_on_drive = os.path.basename(temp_log_filepath)
            pipeline_log_path = os.path.join(
                PROJECT_ROOT_DIR_UI, GLOBAL_CONFIG['paths']['logs_dir'], log_filename_on_drive
            )
            
        else:
            status_message = "Video generation failed! Check logs above for details."

    except Exception as e:
        logger.critical(f"An unexpected error occurred during pipeline execution: {e}", exc_info=True)
        status_message = f"An unexpected error occurred: {e}. Please check the console logs for more details."
    finally:
        if pipeline_file_handler:
            pipeline_file_handler.flush()
            pipeline_file_handler.close()
            logging.getLogger().removeHandler(pipeline_file_handler)
    
    return status_message, None, pipeline_log_path


logger.info("UI Script: User Interface elements defined.")

with gr.Blocks() as demo:
    gr.Markdown(
        """
        # 🎬 AI-Powered Video Generator 🚀
        Generate engaging short videos based on your text prompts using AI models (Gemini, Pexels, Pixabay, Stability AI, Google TTS, Azure TTS).
        ---
        **Instructions:**
        1.  Fill in the parameters below.
        2.  Click 'Generate Video'.
        3.  Wait for the process to complete (can take several minutes).
        4.  The final video and detailed log will be saved to your Google Drive in `project_2.0/output` and `project_2.0/logs` respectively.
        """
    )
    with gr.Row():
        with gr.Column():
            gr.Markdown("## Video Content & Style")
            video_subject_input = gr.Textbox(
                label="Video Subject/Topic (e.g., 'Benefits of daily exercise')",
                value="Healthy lifestyle",
                placeholder="Enter the main subject of your video..."
            )
            video_language_dropdown = gr.Dropdown(
                label="Video Language",
                choices=[lang.value for lang in VideoLanguage],
                value=GLOBAL_CONFIG['video_settings']['default_video_language']
            )
            video_source_type_dropdown = gr.Dropdown(
                label="Visual Asset Source",
                choices=[src.value for src in VideoSourceType],
                value=GLOBAL_CONFIG['video_settings']['default_video_source_type']
            )
            image_prompt_suffix_input = gr.Textbox(
                label="Image/Video Prompt Suffix (for AI generation)",
                placeholder="e.g., 'cinematic, 4k, hyperrealistic' (Optional)",
                value=None, interactive=True
            )
            video_concat_mode_dropdown = gr.Dropdown(
                label="Video Clip Concatenation Mode",
                choices=[mode.value for mode in VideoConcatMode],
                value=GLOBAL_CONFIG['video_settings']['default_concat_mode']
            )
            video_transition_mode_dropdown = gr.Dropdown(
                label="Transition Style Between Clips",
                choices=[mode.value for mode in VideoTransitionMode],
                value=GLOBAL_CONFIG['video_settings']['default_transition_mode']
            )
            video_aspect_ratio_dropdown = gr.Dropdown(
                label="Final Video Aspect Ratio",
                choices=[aspect.value for aspect in VideoAspect],
                value=GLOBAL_CONFIG['video_settings']['default_aspect_ratio']
            )
            max_clip_duration_slider = gr.Slider(
                minimum=5, maximum=60, value=GLOBAL_CONFIG['video_settings']['default_max_clip_duration_s'],
                label="Max Individual Clip Duration (seconds)", step=1
            )
            num_videos_slider = gr.Slider(
                minimum=1, maximum=15, value=GLOBAL_CONFIG['video_settings']['default_num_videos_to_source'],
                label="Number of Visual Assets to Source/Generate", step=1
            )
            final_video_duration_slider = gr.Slider(
                minimum=15, maximum=180, value=GLOBAL_CONFIG['video_settings']['default_final_video_duration_s'],
                label="Desired Final Video Duration (seconds)", step=5
            )

        with gr.Column():
            gr.Markdown("## Audio & Subtitle Settings")
            speech_synthesis_voice_dropdown = gr.Dropdown(
                label="Narration Voice",
                choices=[voice.value for voice in SpeechSynthesisVoice],
                value=GLOBAL_CONFIG['audio_settings']['default_narration_voice']
            )
            enable_subtitles_checkbox = gr.Checkbox(
                label="Enable Subtitles",
                value=GLOBAL_CONFIG['subtitle_settings']['default_enable_subtitles']
            )
            subtitle_font_dropdown = gr.Dropdown(
                label="Subtitle Font",
                choices=[font.value for font in SubtitleFont],
                value=GLOBAL_CONFIG['subtitle_settings']['default_font']
            )
            subtitle_position_dropdown = gr.Dropdown(
                label="Subtitle Position",
                choices=[pos.value for pos in SubtitlePosition],
                value=GLOBAL_CONFIG['subtitle_settings']['default_position']
            )
            subtitle_font_size_slider = gr.Slider(
                minimum=20, maximum=100, value=GLOBAL_CONFIG['subtitle_settings']['default_font_size'],
                label="Subtitle Font Size", step=1
            )
            subtitle_color_input = gr.ColorPicker(
                label="Subtitle Color",
                value=GLOBAL_CONFIG['subtitle_settings']['default_color']
            )
            subtitle_outline_color_input = gr.ColorPicker(
                label="Subtitle Outline Color",
                value=GLOBAL_CONFIG['subtitle_settings']['default_outline_color']
            )
            subtitle_outline_width_slider = gr.Slider(
                minimum=0, maximum=10, value=GLOBAL_CONFIG['subtitle_settings']['default_outline_width'],
                label="Subtitle Outline Width", step=1
            )

    generate_button = gr.Button("Generate Video", variant="primary")
    
    status_output = gr.Textbox(label="Status / Log", lines=5)
    video_output = gr.Video(label="Generated Video (check Drive for final file)", interactive=False)
    download_log_link = gr.File(label="Download Full Log (from Drive)", interactive=False)

    generate_button.click(
        fn=generate_video_ui,
        inputs=[
            video_subject_input,
            video_language_dropdown,
            video_source_type_dropdown,
            image_prompt_suffix_input,
            video_concat_mode_dropdown,
            video_transition_mode_dropdown,
            video_aspect_ratio_dropdown,
            max_clip_duration_slider,
            num_videos_slider,
            final_video_duration_slider,
            speech_synthesis_voice_dropdown,
            enable_subtitles_checkbox,
            subtitle_font_dropdown,
            subtitle_position_dropdown,
            subtitle_font_size_slider,
            subtitle_color_input,
            subtitle_outline_color_input,
            subtitle_outline_width_slider
        ],
        outputs=[status_output, video_output, download_log_link]
    )

logger.info("UI Script: User Interface displayed. Waiting for input.")
demo.launch(debug=True, share=True)
