from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

# Enums for Video Parameters
class VideoLanguage(str, Enum):
    ENGLISH = "English"
    SPANISH = "Spanish"
    FRENCH = "French"
    GERMAN = "German"
    PORTUGUESE = "Portuguese"
    CHINESE = "Chinese"
    JAPANESE = "Japanese"
    KOREAN = "Korean"

class VideoSourceType(str, Enum):
    STOCK_FOOTAGE_PEXELS_PIXABAY = "Stock Footage (Pexels/Pixabay)"
    STOCK_FOOTAGE_PEXELS_ONLY = "Stock Footage (Pexels Only)"
    STOCK_FOOTAGE_PIXABAY_ONLY = "Stock Footage (Pixabay Only)"
    AI_GENERATED_IMAGES = "AI-Generated Images (DALL-E 3, Stable Diffusion)"
    AI_GENERATED_VIDEOS = "AI-Generated Videos (Google Text-to-Video)"

class VideoConcatMode(str, Enum):
    RANDOM_CONCATENATION = "Random Concatenation (Recommended)"
    SEQUENTIAL_CONCATENATION = "Sequential Concatenation"

class VideoTransitionMode(str, Enum):
    FADE = "Fade"
    CROSSFADE = "Crossfade"
    SLIDE = "Slide" # This will map to a generic slide in ffmpeg if implemented, else no transition.
    NONE = "None"

class VideoAspect(str, Enum):
    PORTRAIT_9_16 = "Portrait 9:16 (TikTok/Reels)"
    LANDSCAPE_16_9 = "Landscape 16:9 (YouTube)"
    SQUARE_1_1 = "Square 1:1 (Instagram)"

class SpeechSynthesisVoice(str, Enum):
    # Google Wavenet Voices
    EN_US_WAVENET_A = "en-US-Wavenet-A (Google)"
    EN_US_WAVENET_B = "en-US-Wavenet-B (Google)"
    EN_US_WAVENET_C = "en-US-Wavenet-C (Google)"
    EN_US_WAVENET_D = "en-US-WAVENET-D (Google)"
    EN_US_WAVENET_E = "en-US-WAVENET-E (Google)"
    EN_US_WAVENET_F = "en-US-WAVENET-F (Google)"
    EN_US_WAVENET_G = "en-US-WAVENET-G (Google)"
    EN_US_WAVENET_H = "en-US-WAVENET-H (Google)"
    EN_US_WAVENET_I = "en-US-WAVENET-I (Google)"
    EN_US_WAVENET_J = "en-US-WAVENET-J (Google)"
    # Azure Voices (examples, many more available)
    EN_US_AVA_MULTILINGUAL = "en-US-AvaMultilingualNeural (Azure)"
    EN_US_GUY_MULTILINGUAL = "en-US-GuyMultilingualNeural (Azure)"
    EN_US_NANCY_MULTILINGUAL = "en-US-NancyMultilingualNeural (Azure)"
    # gTTS (offline, basic)
    GTTS_DEFAULT = "gTTS (Basic)"


class SubtitleFont(str, Enum):
    ROBOTO = "Roboto"
    ARIAL = "Arial"
    VERDANA = "Verdana"
    TIMES_NEW_ROMAN = "Times New Roman"
    IMPACT = "Impact"
    COMIC_SANS_MS = "Comic Sans MS"
    MONTSERRAT = "Montserrat"
    OPEN_SANS = "Open Sans"
    LATO = "Lato"
    OSWALD = "Oswald"
    POPPINS = "Poppins"
    SOURCE_SANS_PRO = "Source Sans Pro"
    ANTON = "Anton"
    BASHKIR = "Bashkir" # Example of a less common font

class SubtitlePosition(str, Enum):
    BOTTOM_LEFT = "Bottom Left"
    BOTTOM_CENTER = "Bottom Center"
    BOTTOM_RIGHT = "Bottom Right"
    MIDDLE_LEFT = "Middle Left"
    MIDDLE_CENTER = "Middle Center"
    MIDDLE_RIGHT = "Middle Right"
    TOP_LEFT = "Top Left"
    TOP_CENTER = "Top Center"
    TOP_RIGHT = "Top Right"

    def to_ffmpeg_ass_position(self) -> int:
        """Maps enum to ASS position number for FFmpeg subtitles filter."""
        if self == SubtitlePosition.BOTTOM_LEFT: return 1
        if self == SubtitlePosition.BOTTOM_CENTER: return 2
        if self == SubtitlePosition.BOTTOM_RIGHT: return 3
        if self == SubtitlePosition.MIDDLE_LEFT: return 4
        if self == SubtitlePosition.MIDDLE_CENTER: return 5
        if self == SubtitlePosition.MIDDLE_RIGHT: return 6
        if self == SubtitlePosition.TOP_LEFT: return 7
        if self == SubtitlePosition.TOP_CENTER: return 8
        if self == SubtitlePosition.TOP_RIGHT: return 9
        return 2 # Default to bottom center

@dataclass
class SubtitleEntry:
    text: str
    start_time_s: float
    end_time_s: float

@dataclass
class ImagePrompt:
    text_prompt: str
    image_style: Optional[str] = None
    aspect_ratio: Optional[str] = None # e.g., "16:9", "1:1", "9:16"

@dataclass
class VideoParams:
    video_subject: str
    video_language: VideoLanguage = VideoLanguage.ENGLISH
    video_source_type: VideoSourceType = VideoSourceType.STOCK_FOOTAGE_PEXELS_PIXABAY
    image_prompt_suffix: Optional[str] = None # Used if AI_GENERATED_IMAGES is selected
    video_concat_mode: VideoConcatMode = VideoConcatMode.RANDOM_CONCATENATION
    video_transition_mode: VideoTransitionMode = VideoTransitionMode.FADE
    video_aspect_ratio: VideoAspect = VideoAspect.PORTRAIT_9_16
    max_clip_duration_s: int = 25
    num_videos_to_source_or_generate: int = 5
    final_video_duration_s: int = 60

    speech_synthesis_voice: SpeechSynthesisVoice = SpeechSynthesisVoice.EN_US_WAVENET_C
    enable_subtitles: bool = True
    subtitle_font: SubtitleFont = SubtitleFont.ROBOTO
    subtitle_position: SubtitlePosition = SubtitlePosition.BOTTOM_CENTER
    subtitle_font_size: int = 50
    subtitle_color: str = "white"
    subtitle_outline_color: str = "black"
    subtitle_outline_width: int = 2

    def dict(self):
        # Convert Enum members to their string values for JSON serialization
        return {k: v.value if isinstance(v, Enum) else v for k, v in self.__dict__.items()}
