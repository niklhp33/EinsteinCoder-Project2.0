import logging
import os
import time
from typing import Optional, List

# Local imports
from config import GLOBAL_CONFIG
from models import VideoParams, SubtitleEntry, SubtitleFont, SubtitlePosition, VideoAspect
from utils.cleanup import cleanup_runtime_files, setup_runtime_directories
from utils.gcs_utils import upload_to_gcs
from utils.video_utils import get_video_duration # For general video duration
from utils.audio_utils import combine_audio_tracks, download_background_music, get_audio_duration_ffprobe
from ai_integration.gemini_integration import generate_script_with_gemini
from ai_integration.speech_synthesis import synthesize_narration
from media_processing.video_editor import download_source_clips, combine_and_edit_clips, generate_subtitles_file

logger = logging.getLogger(__name__)

# Define paths from GLOBAL_CONFIG for convenience
RUNTIME_BASE_DIR = GLOBAL_CONFIG['paths']['base_dir']
VIDEO_DOWNLOADS_DIR = os.path.join(RUNTIME_BASE_DIR, GLOBAL_CONFIG['paths']['video_downloads_dir'])
AUDIO_DIR = os.path.join(RUNTIME_BASE_DIR, GLOBAL_CONFIG['paths']['audio_dir'])
IMAGES_DIR = os.path.join(RUNTIME_BASE_DIR, GLOBAL_CONFIG['paths']['images_dir'])
OUTPUT_DIR = os.path.join(RUNTIME_BASE_DIR, GLOBAL_CONFIG['paths']['output_dir'])
TEMP_FILES_DIR = os.path.join(RUNTIME_BASE_DIR, GLOBAL_CONFIG['paths']['temp_files_dir'])
LOGS_DIR = os.path.join(RUNTIME_BASE_DIR, GLOBAL_CONFIG['paths']['logs_dir'])

def generate_video_pipeline(params: VideoParams) -> Tuple[Optional[str], Optional[str]]:
    """
    Main pipeline to generate a short-form video based on provided parameters.
    Returns (path_to_final_video, path_to_log_file).
    """
    logger.info("Starting video generation pipeline...")
    start_time = time.time()

    # 1. Setup Runtime Directories
    setup_runtime_directories()
    log_file_path = os.path.join(LOGS_DIR, f"pipeline_log_{int(start_time)}.txt")
    # Redirect logging to file as well (after initial setup)
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s'))
    logging.getLogger().addHandler(file_handler)
    logger.info(f"Pipeline log file: {log_file_path}")


    final_video_output_path = None
    try:
        # 2. Script Generation
        logger.info("Generating script...")
        script_text = generate_script_with_gemini(
            video_subject=params.video_subject,
            num_paragraphs=3, # Example: hardcode for short-form
            style="engaging, concise, and informative"
        )
        if not script_text:
            logger.error("Script generation failed. Aborting pipeline.")
            return None, log_file_path
        logger.info(f"Generated Script:\n---\n{script_text}\n---")

        # 3. Narration Synthesis
        logger.info("Synthesizing narration...")
        narration_audio_path = synthesize_narration(
            text=script_text,
            audio_output_dir=AUDIO_DIR,
            voice_type=params.speech_synthesis_voice
        )
        if not narration_audio_path:
            logger.error("Narration synthesis failed. Aborting pipeline.")
            return None, log_file_path
        narration_duration = get_audio_duration_ffprobe(narration_audio_path)
        logger.info(f"Narration synthesized. Duration: {narration_duration:.2f}s")
        if narration_duration is None:
            logger.warning("Could not determine narration duration. Setting target video duration to 60s.")
            target_video_duration = 60
        else:
            target_video_duration = narration_duration # Match video duration to narration
        
        # Update params with actual target duration based on narration
        params.final_video_duration_s = int(target_video_duration)


        # 4. Video Clip Sourcing/Generation
        logger.info(f"Sourcing/generating video clips ({params.video_source_type})...")
        downloaded_clips = download_source_clips(
            video_params=params,
            video_downloads_dir=VIDEO_DOWNLOADS_DIR,
            max_clip_duration_s=params.max_clip_duration_s # Use param for individual clip duration
        )
        if not downloaded_clips:
            logger.error("No video clips sourced or generated. Aborting pipeline.")
            return None, log_file_path
        logger.info(f"Sourced/generated {len(downloaded_clips)} clips.")

        # 5. Combine and Edit Video Clips
        logger.info("Combining and editing video clips...")
        base_video_name = f"final_video_{int(time.time())}"
        base_video_path = os.path.join(TEMP_FILES_DIR, f"{base_video_name}_base.mp4")

        combined_video_path = combine_and_edit_clips(
            video_paths=downloaded_clips,
            final_video_duration_s=params.final_video_duration_s,
            video_concat_mode=params.video_concat_mode,
            video_transition_mode=params.video_transition_mode,
            video_aspect_ratio=params.video_aspect_ratio,
            temp_files_dir=TEMP_FILES_DIR,
            output_base_name=base_video_name
        )
        if not combined_video_path:
            logger.error("Video combination/editing failed. Aborting pipeline.")
            return None, log_file_path
        logger.info(f"Base video created: {combined_video_path}")

        # 6. Background Music Integration
        logger.info("Downloading and integrating background music...")
        background_music_path = download_background_music(
            query=GLOBAL_CONFIG['audio_settings']['default_background_music_query'],
            output_dir=AUDIO_DIR
        )
        if not background_music_path:
            logger.warning("Background music download failed. Proceeding without background music.")
            # If music fails, just copy narration to video
            final_audio_path = narration_audio_path
        else:
            final_audio_path = os.path.join(AUDIO_DIR, f"{base_video_name}_final_audio.mp3")
            combined_audio_result = combine_audio_tracks(
                track1_path=narration_audio_path,
                track2_path=background_music_path,
                output_path=final_audio_path,
                track1_volume_db=0.0, # Narration at full volume
                track2_volume_db=GLOBAL_CONFIG['audio_settings']['default_background_music_volume'] # Background music volume
            )
            if not combined_audio_result:
                logger.error("Failed to combine narration and background music. Aborting pipeline.")
                return None, log_file_path
            final_audio_path = combined_audio_result
        logger.info(f"Final audio track prepared: {final_audio_path}")

        # Add final audio to combined video
        video_with_audio_path = os.path.join(TEMP_FILES_DIR, f"{base_video_name}_with_audio.mp4")
        audio_added_result = add_audio_to_video(
            video_path=combined_video_path,
            audio_path=final_audio_path,
            output_path=video_with_audio_path
        )
        if not audio_added_result:
            logger.error("Failed to add audio to video. Aborting pipeline.")
            return None, log_file_path
        final_video_output_path = video_with_audio_path
        logger.info(f"Video with audio created: {final_video_output_path}")

        # 7. Subtitle Generation and Burning
        if params.enable_subtitles:
            logger.info("Generating and burning subtitles...")
            # For simplicity, let's create dummy subtitle entries based on script.
            # In a real implementation, you'd use ASR or detailed script timing.
            dummy_subtitle_entries: List[SubtitleEntry] = []
            words = script_text.split()
            word_duration = narration_duration / len(words) if narration_duration else 0.5 # Approx duration per word
            current_time = 0.0
            segment_length = 5 # words per subtitle segment
            for i in range(0, len(words), segment_length):
                segment_words = words[i:i+segment_length]
                segment_text = " ".join(segment_words)
                start_s = current_time
                end_s = current_time + (len(segment_words) * word_duration)
                dummy_subtitle_entries.append(SubtitleEntry(text=segment_text, start_time_s=start_s, end_time_s=end_s))
                current_time = end_s

            subtitle_file_path = os.path.join(TEMP_FILES_DIR, f"{base_video_name}_subtitles.ass")
            font_path_map = {
                SubtitleFont.ROBOTO: os.path.join(os.path.expanduser('~'), '.fonts', 'Roboto-Regular.ttf'),
                # Add other font paths if you provide them or they're installed in Colab
            }
            # Fallback for font path (Colab usually has some fonts installed)
            default_font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
            chosen_font_path = font_path_map.get(params.subtitle_font, default_font_path)

            ass_file_created = generate_subtitles_file(
                subtitle_entries=dummy_subtitle_entries,
                output_filepath=subtitle_file_path,
                font=params.subtitle_font,
                font_size=params.subtitle_font_size,
                color=params.subtitle_color,
                outline_color=params.subtitle_outline_color,
                outline_width=params.subtitle_outline_width,
                position=params.subtitle_position
            )

            if ass_file_created:
                video_with_subtitles_path = os.path.join(OUTPUT_DIR, f"{base_video_name}_final.mp4")
                subtitles_burnt = add_subtitles_to_video(
                    video_path=final_video_output_path,
                    subtitle_file_path=ass_file_created,
                    output_path=video_with_subtitles_path,
                    font_path=chosen_font_path,
                    font_size=params.subtitle_font_size, # These are mostly illustrative for the prompt, ASS file dictates
                    font_color=params.subtitle_color,     # These are mostly illustrative for the prompt, ASS file dictates
                    outline_color=params.subtitle_outline_color, # These are mostly illustrative for the prompt, ASS file dictates
                    outline_width=params.subtitle_outline_width, # These are mostly illustrative for the prompt, ASS file dictates
                    position=params.subtitle_position.to_ffmpeg_ass_position() # This dictates alignment in ASS
                )
                if subtitles_burnt:
                    final_video_output_path = video_with_subtitles_path
                else:
                    logger.error("Failed to burn subtitles. Final video will be without subtitles.")
            else:
                logger.warning("Failed to generate subtitle ASS file. Skipping subtitle burning.")
        else:
            logger.info("Subtitles disabled as per parameters.")

        logger.info(f"Final video generated: {final_video_output_path}")

        # 8. Upload to Google Drive (via GCS_utils which can write to MyDrive if PROJECT_ROOT_DIR is there)
        # Note: Your instructions say "Final video output to Google Drive"
        # and "Log file persistence to Google Drive".
        # GCS_utils is for GCS bucket. For direct MyDrive persistence from Colab,
        # files are already in PROJECT_ROOT_DIR if you set it right.
        # So we will copy the file from runtime to PROJECT_ROOT_DIR.
        
        drive_output_path = os.path.join(PROJECT_ROOT_DIR, 'output_videos', os.path.basename(final_video_output_path))
        os.makedirs(os.path.dirname(drive_output_path), exist_ok=True)
        
        try:
            shutil.copy(final_video_output_path, drive_output_path)
            logger.info(f"Final video copied to Google Drive: {drive_output_path}")
            # Also copy log file
            drive_log_path = os.path.join(PROJECT_ROOT_DIR, 'logs', os.path.basename(log_file_path))
            os.makedirs(os.path.dirname(drive_log_path), exist_ok=True)
            shutil.copy(log_file_path, drive_log_path)
            logger.info(f"Log file copied to Google Drive: {drive_log_path}")
        except Exception as e:
            logger.error(f"Failed to copy final video or log to Google Drive: {e}", exc_info=True)
            # Proceed with runtime paths if Drive copy fails

        end_time = time.time()
        logger.info(f"Pipeline completed in {end_time - start_time:.2f} seconds.")

        return final_video_output_path, log_file_path

    except Exception as e:
        logger.critical(f"An unhandled error occurred in the pipeline: {e}", exc_info=True)
        return None, log_file_path
    finally:
        # Clean up temporary runtime files (optional, but good for Colab limits)
        logger.info("Cleaning up runtime files...")
        cleanup_runtime_files()
        logging.getLogger().removeHandler(file_handler) # Remove file handler to prevent multiple writes on re-run
