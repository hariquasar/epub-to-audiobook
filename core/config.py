"""Configuration constants, genre definitions, and specialized style templates."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

DEFAULT_MODEL_DIR = Path("/Users/hoyinshum/tools/ai/qwen3-tts/Qwen3-TTS-12Hz-1.7B-CustomVoice")
DEFAULT_MODEL_ID = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
DEFAULT_SPEAKER = "Uncle_Fu"

# Target character limit per audio chunk (never split across sentences)
DEFAULT_MAX_CHARS = 200

# Minimum audio duration per character in seconds for duration audit
MIN_SECONDS_PER_CHAR = 0.14

# Maximum allowed silence duration between sentences in seconds
MAX_SILENCE_SECONDS = 0.30

# Maximum audio token generation limit (allows up to ~90s speech per chunk)
DEFAULT_MAX_NEW_TOKENS = 1200

# ==============================================================================
# Genre-Specific Narration Presets
# ==============================================================================

FICTION_PRESETS: Dict[str, str] = {
    "fiction_storyteller": (
        "一位四十五至五十五岁的男性说书人。使用标准现代普通话，字正腔圆，清晰区分平翘舌与前后鼻音；"
        "全程按普通话音系与声调发音，不带粤语口音、港式普通话韵律或其他地方口音，不使用粤语词汇或语气助词。"
        "低沉男中音，胸腔共鸣稳定，音色浑厚、带少量自然砂砾感；沉稳，有人情味，有江湖故事感。"
        "普通叙述要自然流畅、有向前推进的节奏，语速中等偏快，不拖字，不刻意压慢，也不平板。"
        "交代场景和人物时清楚稳健；打斗、危急、秘密揭晓、感叹和直接引语时可以明显增强节奏、重音、音高和情绪，"
        "但保持自然，不喊叫，不用戏曲腔。直接引语可模仿角色；引语结束后回到有推进力的低沉旁白。"
        "句内停顿短促，句末自然收束；不要加入长时间沉默或戏剧性空白。"
        "每次朗读必须完整说完收到的全部文字，直到最后一个字和标点；不得在段落中途停止。"
        "不要新增、删减、改写任何文字。"
    ),
    "fiction_dramatic": (
        "一位极富表现力的小说演播家。使用标准普通话，音色富有磁性与张力。"
        "叙述生动抓人，节奏紧凑跌宕；在描写紧张冲突、悬疑反转及人物情绪爆发时，情绪饱满充沛，"
        "对话直接引语自然带入角色性格与喜怒哀乐，旁白部分沉着有力，引人入胜。"
        "每次朗读必须完整说完收到的全部文字，不得在段落中途停止，不得修改文字。"
    ),
    "fiction_immersive": (
        "一位沉浸式文学小说旁白员。标准现代普通话，音色温和醇厚、低回悠扬。"
        "语速平缓适中，重在营造静谧、深邃的故事氛围与画面感；句末收束自然舒缓。"
        "每次朗读必须完整说完收到的全部文字，不得在段落中途停止，不得修改文字。"
    ),
}

NONFICTION_PRESETS: Dict[str, str] = {
    "nonfiction_business": (
        "一位专业干练的商业与经管类有声书领读人。使用标准现代普通话，咬字清晰利落，发音端正干脆。"
        "音色沉稳自信、具有权威感与说服力。语速匀速适中（约每分钟240字），节奏条理分明，不拖泥带水。"
        "朗读数据、专业术语、核心观点及论据时重音准确明晰，整体风格客观理性、结构感强，不带夸张的戏剧化情绪。"
        "句内停顿干脆，句末收束干净，严禁长时间空白。"
        "每次朗读必须完整说完收到的全部文字，直到最后一个标点，不得中途停止，不得增删文字。"
    ),
    "nonfiction_documentary": (
        "一位纪录片与历史科普解说专家。使用标准普通话，音色浑厚深沉、大气庄重。"
        "叙事宏大沉稳，娓娓道来，既有历史厚重感又保持科学严谨性。语调平稳克制，突出知识传递的清晰度与沉浸感。"
        "每次朗读必须完整说完收到的全部文字，不得在段落中途停止，不得修改文字。"
    ),
    "nonfiction_academic": (
        "一位大学学者与学术讲座讲师。标准普通话，语调温文尔雅、逻辑严密、循循善诱。"
        "语速平稳适中，对概念定义、逻辑推导和分点论述交代得层次分明、通俗易懂。"
        "每次朗读必须完整说完收到的全部文字，不得中途停止，不得修改文字。"
    ),
    "nonfiction_mindfulness": (
        "一位哲学、心理与个人成长类有声书导师。标准普通话，音色温暖柔和、澄澈安宁。"
        "语调亲切真诚、富有启发感与内在力量。语速舒缓从容，停顿自然，给人以平静思考的空间。"
        "每次朗读必须完整说完收到的全部文字，不得中途停止，不得修改文字。"
    ),
}

# Unified Master Preset Map
STYLE_PRESETS: Dict[str, str] = {
    **FICTION_PRESETS,
    **NONFICTION_PRESETS,
    # Backward compatibility aliases
    "storyteller": FICTION_PRESETS["fiction_storyteller"],
    "calm_narrator": NONFICTION_PRESETS["nonfiction_documentary"],
    "energetic": FICTION_PRESETS["fiction_dramatic"],
}

# Genre-specific audio tuning defaults
GENRE_CONFIGS = {
    "fiction": {
        "default_style": "fiction_storyteller",
        "default_speaker": "Uncle_Fu",
        "max_silence_s": 0.35,  # Slightly more dramatic breathing pause for novels
        "temperature": 0.62,
        "top_p": 0.88,
    },
    "nonfiction": {
        "default_style": "nonfiction_business",
        "default_speaker": "Uncle_Fu",
        "max_silence_s": 0.25,  # Tighter pauses for efficient, clean information absorption
        "temperature": 0.45,  # Lower temperature for maximum stability and clarity
        "top_p": 0.82,
    },
}


def get_presets_by_genre(genre: str = "fiction") -> Dict[str, str]:
    """Return available style presets for the given genre."""
    if genre.lower() == "nonfiction":
        return NONFICTION_PRESETS
    return FICTION_PRESETS
