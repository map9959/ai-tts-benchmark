import os

API_KEYS = {
    'cartesia': os.environ.get('CARTESIA_API_KEY'),
    'deepgram': os.environ.get('DEEPGRAM_API_KEY'),
    'rime': os.environ.get('RIME_API_KEY'),
    'elevenlabs': os.environ.get('ELEVENLABS_API_KEY')
}
SAMPLE_RATE = 8000