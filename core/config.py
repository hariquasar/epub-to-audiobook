"""Configuration constants and style templates for Qwen3-TTS Audiobook Generator."""

from __future__ import annotations

from pathlib import Path

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

# Preset style templates for narration
STYLE_PRESETS = {
    "storyteller": (
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
    "calm_narrator": (
        "一位成熟稳重的男性旁白播音员。使用标准现代普通话，字正腔圆，音色低沉浑厚、清晰自然。"
        "叙述语速平稳适中，语气平静克制，句内停顿自然，句末收束干净。"
        "每次朗读必须完整说完收到的全部文字，不得在段落中途停止，不得新增、删减、改写任何文字。"
    ),
    "energetic": (
        "一位富有激情的男性评书说书人。标准现代普通话，咬字有力，节奏跌宕起伏，"
        "交代情节生动传神，打斗与冲突时刻情绪饱满昂扬，语气富有张力。"
        "每次朗读必须完整说完收到的全部文字，不得中途停止，不得改写文字。"
    ),
}
