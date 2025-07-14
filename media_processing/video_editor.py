import os
import logging
import random
from typing import List, Optional, Tuple, Any

from utils.ffmpeg_utils import concatenate_videos, add_audio_to_video, add_subtitles_to_video
from utils.video_utils import get_video_duration, search_pexels_videos, search_pixabay_videos, download_video_clip
from ai_integration.image_video_generation import generate_image_with_imagen, generate_video_with_ttv_api
from config import GLOBAL_CONFIG
from models import VideoTransitionMode, VideoSourceType, VideoAspect, VideoConcatMode, SubtitleEntry, SubtitleFont, SubtitlePosition

logger = logging.getLogger(__name__)

def generate_subtitles_file(
    subtitle_entries: List[SubtitleEntry],
    output_filepath: str,
    font: SubtitleFont,
    font_size: int,
    color: str,
    outline_color: str,
    outline_width: int,
    position: SubtitlePosition
) -> Optional[str]:
    """
    Generates an ASS (Advanced SubStation Alpha) subtitle file from a list of subtitle entries.
    Includes styling information for FFmpeg to burn in.
    """
    logger.info(f"Generating ASS subtitle file: {output_filepath}")

    # Map color names to hex (e.g., 'white' -> '&HFFFFFF&', 'black' -> '&H000000&')
    # ASS colors are BGRA, so ABGR hex. FFmpeg expects ARGB or RGBA typically.
    # We'll use basic HTML-style color names and hope FFmpeg's ASS parser handles them,
    # or rely on direct hex:
    # ASS colors are usually BGR hex like &HBBGGRR&. Let's use standard hex like RRGGBB.
    # And convert to ASS format if needed (usually done by client, or just use name)

    # Simplified color mapping for ASS PrimaryColour (ARGB, but in reverse order for ASS: BBGGRR)
    # FFmpeg subtitles filter generally handles common color names.
    # For precise hex, we would map "white" to 0xFFFFFF and then reorder to ASS &HBBGGRR
    # e.g., white is &HFFFFFF, black is &H000000

    # For now, let's keep it simple with common color names for the ASS file.
    # ASS file format directly specifies font path for custom fonts.
    # We will assume a common font path like /usr/share/fonts/truetype/dejavu if font_path not found.
    # For custom fonts, the user needs to provide a direct path or ensure it's installed.

    ass_content = f"""[Script Info]
ScriptType: v4.00+
Collisions: Normal
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font.value},{font_size},{color},{color},{outline_color},{outline_color},0,0,0,0,100,100,0,0,1,{outline_width},0,{position.to_ffmpeg_ass_position()},0,0,0,1
"""
    for entry in subtitle_entries:
        start_time = time.strftime('%H:%M:%S', time.gmtime(entry.start_time_s)) + f".{int((entry.start_time_s % 1) * 100):02d}"
        end_time = time.strftime('%H:%M:%S', time.gmtime(entry.end_time_s)) + f".{int((entry.end_time_s % 1) * 100):02d}"
        # ASS dialogue line: Dialogue: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
        ass_content += f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{entry.text}\n"

    try:
        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(ass_content)
        logger.info(f"Subtitle file created successfully: {output_filepath}")
        return output_filepath
    except Exception as e:
        logger.error(f"Failed to write subtitle file: {e}", exc_info=True)
        return None

def download_source_clips(video_params: Any, video_downloads_dir: str, max_clip_duration_s: int) -> List[str]:
    """
    Downloads video clips based on the selected source type.
    """
    downloaded_clip_paths = []
    
    # Define target resolution for clips based on aspect ratio (e.g., 9:16 for portrait)
    target_width = 1080 # Default for TikTok/Reels portrait
    target_height = 1920

    if video_params.video_source_type == VideoSourceType.PORTRAIT_9_16:
        target_width, target_height = 1080, 1920
    elif video_params.video_source_type == VideoSourceType.LANDSCAPE_16_9:
        target_width, target_height = 1920, 1080
    elif video_params.video_source_type == VideoSourceType.SQUARE_1_1:
        target_width, target_height = 1080, 1080
        
    os.makedirs(video_downloads_dir, exist_ok=True)

    if video_params.video_source_type in [VideoSourceType.STOCK_FOOTAGE_PEXELS_PIXABAY, VideoSourceType.STOCK_FOOTAGE_PEXELS_ONLY]:
        logger.info(f"Sourcing videos from Pexels for query: {video_params.video_subject}")
        pexels_api_key = GLOBAL_CONFIG['api_keys']['pexels_api_key']
        pexels_videos = search_pexels_videos(
            query=video_params.video_subject,
            api_key=pexels_api_key,
            orientation='portrait' if video_params.video_aspect_ratio == VideoAspect.PORTRAIT_9_16 else 'landscape',
            per_page=video_params.num_videos_to_source_or_generate
        )
        for i, video_data in enumerate(pexels_videos):
            # Find the best quality portrait video file
            best_video_url = None
            for v_file in video_data.get('video_files', []):
                # Prioritize 'hd' or 'sd' and correct orientation
                if v_file.get('quality') in ['hd', 'sd'] and \
                   ((video_params.video_aspect_ratio == VideoAspect.PORTRAIT_9_16 and v_file.get('height',0) > v_file.get('width',0)) or \
                    (video_params.video_aspect_ratio == VideoAspect.LANDSCAPE_16_9 and v_file.get('width',0) > v_file.get('height',0)) or \
                    (video_params.video_aspect_ratio == VideoAspect.SQUARE_1_1 and v_file.get('width',0) == v_file.get('height',0) and v_file.get('width',0) > 0)):
                    best_video_url = v_file['link']
                    break
            
            if best_video_url:
                output_filepath = os.path.join(video_downloads_dir, f"pexels_clip_{i}.mp4")
                downloaded_path = download_video_clip(best_video_url, output_filepath)
                if downloaded_path:
                    downloaded_clip_paths.append(downloaded_path)
                    if len(downloaded_clip_paths) >= video_params.num_videos_to_source_or_generate:
                        break # Stop once we have enough clips
            else:
                logger.warning(f"No suitable Pexels video link found for clip {i} for query '{video_params.video_subject}'")

    if video_params.video_source_type in [VideoSourceType.STOCK_FOOTAGE_PEXELS_PIXABAY, VideoSourceType.STOCK_FOOTAGE_PIXABAY_ONLY]:
        logger.info(f"Sourcing videos from Pixabay for query: {video_params.video_subject}")
        pixabay_api_key = GLOBAL_CONFIG['api_keys']['pixabay_api_key']
        pixabay_videos = search_pixabay_videos(
            query=video_params.video_subject,
            api_key=pixabay_api_key,
            per_page=video_params.num_videos_to_source_or_generate
        )
        for i, video_data in enumerate(pixabay_videos):
            # Pixabay offers tiny, small, medium, large. Choose 'medium' or 'large'
            video_url = video_data.get('videos', {}).get('medium', {}).get('url')
            if video_url:
                output_filepath = os.path.join(video_downloads_dir, f"pixabay_clip_{i}.mp4")
                downloaded_path = download_video_clip(video_url, output_filepath)
                if downloaded_path:
                    downloaded_clip_paths.append(downloaded_path)
                    if len(downloaded_clip_paths) >= video_params.num_videos_to_source_or_generate:
                        break # Stop once we have enough clips
            else:
                logger.warning(f"No suitable Pixabay video link found for clip {i} for query '{video_params.video_subject}'")

    if video_params.video_source_type == VideoSourceType.AI_GENERATED_IMAGES:
        logger.info(f"Generating AI images for video: {video_params.video_subject}")
        for i in range(video_params.num_videos_to_source_or_generate):
            prompt = video_params.video_subject
            if video_params.image_prompt_suffix:
                prompt += f", {video_params.image_prompt_suffix}"
            
            # Use fixed aspect ratio for AI images matching desired video aspect
            img_aspect_ratio = video_params.video_aspect_ratio.value.split(' ')[1] # e.g., '9:16'
            
            image_path = generate_image_with_imagen(
                prompt=prompt,
                image_style="photorealistic", # Could be configurable via UI
                aspect_ratio=img_aspect_ratio
            )
            if image_path:
                # Convert image to short video clip (e.g., 5 seconds)
                image_video_path = os.path.join(video_downloads_dir, f"ai_image_clip_{i}.mp4")
                
                # Use ffmpeg to convert static image to a video clip
                # ffmpeg -y -loop 1 -i image.png -c:v libx264 -t 5 -pix_fmt yuv420p video.mp4
                cmd = [
                    'ffmpeg', '-y',
                    '-loop', '1',
                    '-i', shlex.quote(image_path),
                    '-t', str(video_params.max_clip_duration_s), # Duration of image clip
                    '-vf', f"scale={target_width}:{target_height}:force_original_aspect_ratio=increase,crop={target_width}:{target_height},setsar=1",
                    '-c:v', 'libx264', '-preset', 'fast', '-crf', '23', '-pix_fmt', 'yuv420p',
                    shlex.quote(image_video_path)
                ]
                stdout, stderr, returncode = run_shell_command(cmd, check_error=False, timeout=60)
                if returncode == 0:
                    downloaded_clip_paths.append(image_video_path)
                else:
                    logger.error(f"Failed to convert AI image {image_path} to video: {stderr}")

    if video_params.video_source_type == VideoSourceType.AI_GENERATED_VIDEOS:
        logger.info(f"Generating AI videos for topic: {video_params.video_subject}")
        for i in range(video_params.num_videos_to_source_or_generate):
            prompt = video_params.video_subject
            # Assuming TTV API can generate clips of a certain duration
            video_path = generate_video_with_ttv_api(
                script_segment=prompt,
                duration_seconds=video_params.max_clip_duration_s,
                video_style="cinematic" # Could be configurable
            )
            if video_path:
                downloaded_clip_paths.append(video_path)

    logger.info(f"Finished sourcing/generating clips. Total clips: {len(downloaded_clip_paths)}")
    return downloaded_clip_paths


def combine_and_edit_clips(
    video_paths: List[str],
    final_video_duration_s: int,
    video_concat_mode: VideoConcatMode,
    video_transition_mode: VideoTransitionMode,
    video_aspect_ratio: VideoAspect,
    temp_files_dir: str,
    output_base_name: str
) -> Optional[str]:
    """
    Manages the concatenation and basic editing of video clips.
    """
    logger.info(f"Starting combine and edit clips process.")

    if not video_paths:
        logger.error("No video paths provided to combine and edit.")
        return None

    # Determine target dimensions based on aspect ratio
    target_width, target_height = 0, 0
    if video_aspect_ratio == VideoAspect.PORTRAIT_9_16:
        target_width, target_height = 1080, 1920
    elif video_aspect_ratio == VideoAspect.LANDSCAPE_16_9:
        target_width, target_height = 1920, 1080
    elif video_aspect_ratio == VideoAspect.SQUARE_1_1:
        target_width, target_height = 1080, 1080
    else:
        logger.error(f"Unsupported video aspect ratio: {video_aspect_ratio}. Defaulting to 9:16.")
        target_width, target_height = 1080, 1920

    # Handle concat mode
    if video_concat_mode == VideoConcatMode.RANDOM_CONCATENATION:
        random.shuffle(video_paths)
        logger.info("Video concatenation order randomized.")
    elif video_concat_mode == VideoConcatMode.SEQUENTIAL_CONCATENATION:
        logger.info("Video concatenation order is sequential.")

    final_concat_output = os.path.join(temp_files_dir, f"{output_base_name}_concatenated.mp4")

    # Call ffmpeg_utils for concatenation
    concatenated_video_path = concatenate_videos(
        video_paths=video_paths,
        output_path=final_concat_output,
        target_width=target_width,
        target_height=target_height,
        target_duration=float(final_video_duration_s),
        transition=video_transition_mode.value.lower(),
        temp_files_dir=temp_files_dir
    )

    if not concatenated_video_path:
        logger.error("Failed to concatenate videos.")
        return None

    logger.info(f"Video clips combined into: {concatenated_video_path}")
    return concatenated_video_path
