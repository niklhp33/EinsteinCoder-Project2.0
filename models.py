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
    # Google Wavenet Voices (high quality, but requires Google Cloud TTS API)
    EN_US_WAVENET_A = "en-US-Wavenet-A"
    EN_US_WAVENET_C = "en-US-Wavenet-C"
    EN_US_WAVENET_D = "en-US-WAVENET-D"
    EN_US_WAVENET_E = "en-US-WAVENET-E"
    EN_US_WAVENET_F = "en-US-WAVENET-F"
    EN_US_WAVENET_G = "en-US-WAVENET-G"
    EN_US_WAVENET_H = "en-US-WAVENET-H"
    EN_US_WAVENET_I = "en-US-WAVENET-I"
    EN_US_WAVENET_J = "en-US-WAVENET-J"
    EN_US_WAVENET_K = "en-US-WAVENET-K"
    EN_US_WAVENET_L = "en-US-WAVENET-L"
    EN_US_WAVENET_M = "en-US-WAVENET-M"

    # Google Standard Voices (lower quality, but generally free/lower cost)
    EN_US_STANDARD_A = "en-US-Standard-A"
    EN_US_STANDARD_B = "en-US-Standard-B"

    # Azure Voices (if Azure TTS is integrated)
    EN_US_AZURE_CHRISTOPHER = "en-US-ChristopherNeural (Azure)"
    EN_US_AZURE_ANA = "en-US-AnaNeural (Azure)"
    
    # gTTS (free, simpler Google TTS API)
    GTTS_EN = "en (gTTS)"
    GTTS_ES = "es (gTTS)"

class SubtitleFont(str, Enum):
    ROBOTO = "Roboto"
    ARIAL = "Arial"
    VERDANA = "Verdana"
    IMPACT = "Impact"

class SubtitlePosition(str, Enum):
    TOP_CENTER = "Top Center"
    BOTTOM_CENTER = "Bottom Center"
    CENTER = "Center"
    TOP_LEFT = "Top Left"
    TOP_RIGHT = "Top Right"
    BOTTOM_LEFT = "Bottom Left"
    BOTTOM_RIGHT = "Bottom Right"

    def to_ass_alignment(self) -> int:
        """Converts to ASS alignment codes (1-9 on numpad)."""
        if self == SubtitlePosition.BOTTOM_LEFT: return 1
        if self == SubtitlePosition.BOTTOM_CENTER: return 2
        if self == SubtitlePosition.BOTTOM_RIGHT: return 3
        if self == SubtitlePosition.CENTER: return 5
        if self == SubtitlePosition.TOP_LEFT: return 7
        if self == SubtitlePosition.TOP_CENTER: return 8
        if self == SubtitlePosition.TOP_RIGHT: return 9
        return 2

@dataclass
class VideoParams:
    video_subject: str
    video_language: VideoLanguage = VideoLanguage.ENGLISH
    video_source_type: VideoSourceType = VideoSourceType.STOCK_FOOTAGE_PEXELS_PIXABAY
    image_prompt_suffix: Optional[str] = None
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
        return {k: v.value if isinstance(v, Enum) else v for k, v in self.__dict__.items()}


@dataclass
class SubtitleEntry:
    text: str
    start_time: float
    end_time: float

@dataclass
class ImagePrompt:
    text_prompt: str
    image_path: Optional[str] = None
    model_name: Optional[str] = None
