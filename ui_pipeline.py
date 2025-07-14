import gradio as gr
import logging
import os
import shutil
import time

from config import GLOBAL_CONFIG
from models import VideoParams, VideoLanguage, VideoSourceType, VideoConcatMode, VideoTransitionMode, VideoAspect, SpeechSynthesisVoice, SubtitleFont, SubtitlePosition
from pipeline import generate_video_pipeline # Import the main pipeline

logger = logging.getLogger(__name__)

# Ensure logging is configured before Gradio starts
if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Gradio Interface Functions ---

def run_pipeline_ui(
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
    """
    Wrapper function to run the video generation pipeline from Gradio UI.
    """
    logger.info("Gradio UI: Video generation started.")
    
    # Map string inputs from Gradio to Enum types for VideoParams
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
    except ValueError as e:
        logger.error(f"Gradio UI: Invalid input parameter: {e}")
        return None, None, f"Error: Invalid input parameter: {e}. Please check your selections."

    status_message = "Video generation in progress... Check logs for details."
    
    # Call the main pipeline function
    final_video_path, log_path = generate_video_pipeline(params)

    if final_video_path and os.path.exists(final_video_path):
        final_status = f"Video generation completed successfully! Output: {final_video_path}"
        logger.info(final_status)
        return final_video_path, log_path, final_status
    else:
        final_status = f"Video generation failed. Check log file for errors: {log_path}"
        logger.error(final_status)
        return None, log_path, final_status

def launch_gradio_ui():
    """Launches the Gradio user interface."""
    logger.info("Launching Gradio UI...")

    # Determine default values from GLOBAL_CONFIG
    default_video_params = VideoParams(
        video_subject="default subject", # This will be overridden by UI input
        video_source_type=VideoSourceType(GLOBAL_CONFIG['video_settings']['default_video_source_type']),
        video_concat_mode=VideoConcatMode(GLOBAL_CONFIG['video_settings']['default_concat_mode']),
        video_transition_mode=VideoTransitionMode(GLOBAL_CONFIG['video_settings']['default_transition_mode']),
        video_language=VideoLanguage(GLOBAL_CONFIG['video_settings']['default_video_language']),
        speech_synthesis_voice=SpeechSynthesisVoice(GLOBAL_CONFIG['audio_settings']['default_narration_voice']),
        enable_subtitles=GLOBAL_CONFIG['subtitle_settings']['default_enable_subtitles'],
        subtitle_font=SubtitleFont(GLOBAL_CONFIG['subtitle_settings']['default_font']),
        subtitle_position=SubtitlePosition(GLOBAL_CONFIG['subtitle_settings']['default_position']),
        subtitle_font_size=GLOBAL_CONFIG['subtitle_settings']['default_font_size'],
        subtitle_color=GLOBAL_CONFIG['subtitle_settings']['default_color'],
        subtitle_outline_color=GLOBAL_CONFIG['subtitle_settings']['default_outline_color'],
        subtitle_outline_width=GLOBAL_CONFIG['subtitle_settings']['default_outline_width']
    )

    with gr.Blocks(theme=gr.themes.Soft()) as demo:
        gr.Markdown("# 🎬 Einstein Coder - Automated Short-Form Video Generation")
        gr.Markdown("Enter your video subject and customize settings to generate a short video.")

        with gr.Row():
            with gr.Column():
                gr.Markdown("### 📝 Script & Voice Settings")
                video_subject = gr.Textbox(label="Video Subject/Topic", placeholder="e.g., 'Benefits of AI in daily life'", interactive=True)
                video_language = gr.Dropdown(
                    label="Video Language",
                    choices=[e.value for e in VideoLanguage],
                    value=default_video_params.video_language.value,
                    interactive=True
                )
                speech_synthesis_voice = gr.Dropdown(
                    label="Narration Voice",
                    choices=[e.value for e in SpeechSynthesisVoice],
                    value=default_video_params.speech_synthesis_voice.value,
                    interactive=True
                )
            with gr.Column():
                gr.Markdown("### 🎥 Video Source & Editing")
                video_source_type = gr.Dropdown(
                    label="Video Source Type",
                    choices=[e.value for e in VideoSourceType],
                    value=default_video_params.video_source_type.value,
                    interactive=True
                )
                image_prompt_suffix = gr.Textbox(
                    label="AI Image Prompt Suffix (if AI Images selected)",
                    placeholder="e.g., 'futuristic, hyperrealistic'",
                    lines=1,
                    interactive=True
                )
                video_aspect_ratio = gr.Radio(
                    label="Video Aspect Ratio",
                    choices=[e.value for e in VideoAspect],
                    value=default_video_params.video_aspect_ratio.value,
                    interactive=True
                )
                video_concat_mode = gr.Dropdown(
                    label="Video Concatenation Mode",
                    choices=[e.value for e in VideoConcatMode],
                    value=default_video_params.video_concat_mode.value,
                    interactive=True
                )
                video_transition_mode = gr.Dropdown(
                    label="Video Transition Mode",
                    choices=[e.value for e in VideoTransitionMode],
                    value=default_video_params.video_transition_mode.value,
                    interactive=True
                )
                max_clip_duration_s = gr.Slider(minimum=5, maximum=30, value=default_video_params.max_clip_duration_s, step=1, label="Max Individual Clip Duration (s)")
                num_videos_to_source_or_generate = gr.Slider(minimum=3, maximum=15, value=default_video_params.num_videos_to_source_or_generate, step=1, label="Number of Clips to Source/Generate")
                final_video_duration_s = gr.Slider(minimum=15, maximum=120, value=default_video_params.final_video_duration_s, step=5, label="Target Final Video Duration (s)")

            with gr.Column():
                gr.Markdown("### 📝 Subtitle Settings")
                enable_subtitles = gr.Checkbox(label="Enable Subtitles", value=default_video_params.enable_subtitles, interactive=True)
                subtitle_font = gr.Dropdown(
                    label="Font",
                    choices=[e.value for e in SubtitleFont],
                    value=default_video_params.subtitle_font.value,
                    interactive=True
                )
                subtitle_position = gr.Dropdown(
                    label="Position",
                    choices=[e.value for e in SubtitlePosition],
                    value=default_video_params.subtitle_position.value,
                    interactive=True
                )
                subtitle_font_size = gr.Slider(minimum=20, maximum=100, value=default_video_params.subtitle_font_size, step=1, label="Font Size")
                subtitle_color = gr.ColorPicker(label="Font Color", value=default_video_params.subtitle_color, interactive=True)
                subtitle_outline_color = gr.ColorPicker(label="Outline Color", value=default_video_params.subtitle_outline_color, interactive=True)
                subtitle_outline_width = gr.Slider(minimum=0, maximum=10, value=default_video_params.subtitle_outline_width, step=1, label="Outline Width")
        
        generate_btn = gr.Button("🚀 Generate Video", variant="primary")

        with gr.Row():
            video_output = gr.Video(label="Generated Video", interactive=False)
        with gr.Row():
            log_output = gr.File(label="Log File", interactive=False)
        with gr.Row():
            status_text = gr.Textbox(label="Status", interactive=False, lines=2)

        generate_btn.click(
            fn=run_pipeline_ui,
            inputs=[
                video_subject,
                video_language,
                video_source_type,
                image_prompt_suffix,
                video_concat_mode,
                video_transition_mode,
                video_aspect_ratio,
                max_clip_duration_s,
                num_videos_to_source_or_generate,
                final_video_duration_s,
                speech_synthesis_voice,
                enable_subtitles,
                subtitle_font,
                subtitle_position,
                subtitle_font_size,
                subtitle_color,
                subtitle_outline_color,
                subtitle_outline_width
            ],
            outputs=[video_output, log_output, status_text]
        )
    
    demo.launch(debug=True, share=True)

if __name__ == "__main__":
    launch_gradio_ui()
