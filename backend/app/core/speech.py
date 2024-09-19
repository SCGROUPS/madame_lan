import os
import uuid
import re
import asyncio

import emoji
from azure.cognitiveservices.speech import SpeechConfig, SpeechSynthesizer, AudioConfig

from ..config import AUDIO_TMP_DIR, Config, LOGGER, async_timeit


SPEECH_CONFIG = SpeechConfig(subscription=Config.SPEECH_KEY, region=Config.SPEECH_REGION)
SPEECH_CONFIG.speech_synthesis_voice_name = Config.TTS_VOICE


@async_timeit()
async def generate_speech_audio(text: str, voice: str) -> str:
    try:
        audio_filename = f"{uuid.uuid4()}.wav"
        audio_path = os.path.join(AUDIO_TMP_DIR, audio_filename)
        audio_output = AudioConfig(filename=audio_path)
        voice_name = Config.LANGUAGES[voice]['voice_name']
        SPEECH_CONFIG.speech_synthesis_voice_name = voice_name
        synthesizer = SpeechSynthesizer(speech_config=SPEECH_CONFIG, audio_config=audio_output)
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, lambda: synthesizer.speak_text_async(text).get())
    except Exception as e:
        LOGGER.error("Exception: {}".format(e))
    return f"{audio_path}"

def remove_emoji(text):
    return emoji.replace_emoji(text, replace='')

def replace_markdown_links_with_urls(text):
    markdown_link_pattern = re.compile(r'\[([^\]]+)\]\((http[^\)]+)\)')
    matches = markdown_link_pattern.findall(text)
    for match in matches:
        full_link = match[0]
        url = match[1]
        text = text.replace(f'[{full_link}]({url})', url)
    return text
