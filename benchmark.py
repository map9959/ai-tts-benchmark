import asyncio
import pyaudio
import requests
import random
import string
from utils import DIGIT_MAP, NATO_PHONETIC_MAP
from config import API_KEYS, SAMPLE_RATE
from cartesia import Cartesia
from deepgram import DeepgramClient, SpeakOptions
from elevenlabs import ElevenLabs, VoiceSettings, save
from pydub import AudioSegment
import os

BACKENDS = ['cartesia', 'rime', 'deepgram', 'elevenlabs']
VOICES_PER_SERVICE = 4

cartesia_client = Cartesia(api_key=API_KEYS['cartesia'])
voices = cartesia_client.voices.list()

cartesia_voice_list = [('Female Nurse', 'f9836c6e-a0bd-460e-9d3c-f7299fa60f94'),
                        ('Southern Woman', '5c42302c-194b-4d0c-ba1a-8cb485c84ab9'),
                        ('Laidback Woman', '21b81c14-f85b-436d-aff5-43f2e788ecf8'),
                        ('Sarah', '694f9389-aac1-45b6-b726-9d9369183238')]
cartesia_voices = []
for _, voice_id in cartesia_voice_list:
   cartesia_voices.append(cartesia_client.voices.get(id=voice_id))

rime_voices = ['kendra', 'marissa', 'eva', 'selena']

deepgram_voices = ['asteria', 'luna', 'stella', 'hera']

elevenlabs_voices = [('Crystal', 'tRhabdS7JjlQ0lVEImuM'),
                        ('Aria', '9BWtsMINqrJLrRacOk9x'),
                        ('Tanya', 'Bwff1jnzl1s94AEcntUq'),
                        ('Jessica', 'cgSgspJ2msm6clMCkdW9')]


output_format = {
    "container": "raw",
    "encoding": "pcm_s16le",
    "sample_rate": SAMPLE_RATE,
}
model_id = "sonic-english"

def id_formatter(id, backend_name):
    res = ''
    for i, char in enumerate(id):
        if char.isalpha():
            if char.lower() == 'a' and backend_name in ['cartesia', 'deepgram', 'elevenlabs']:
                    res += 'A as in Alpha'
            else:
                res += f'{NATO_PHONETIC_MAP[char.lower()]}'
        elif char.isdigit():
            res += f'{DIGIT_MAP[char]}'

        if i != len(id) - 1:
            match backend_name:
                case 'cartesia':
                    res += ' -, '
                case 'rime':
                    res += '. '
                case 'deepgram':
                    res += '. . '
                case 'elevenlabs':
                    res += ', <break time="0.25s" /> '
    return res

async def audio_output_cartesia(transcript, voice, filetag):
    stream = open(f"cartesia-{voice['name']}-{filetag}.pcm", "wb")
    p = pyaudio.PyAudio()

    # Set up the websocket connection
    ws = cartesia_client.tts.websocket()

    # Generate and stream audio using the websocket
    for output in ws.send(
        model_id=model_id,
        transcript=transcript,
        voice_embedding=voice["embedding"],
        stream=True,
        output_format=output_format,
    ):
        buffer = output["audio"]

        # Write the audio data to the stream
        stream.write(buffer)

    p.terminate()

    ws.close()  # Close the websocket connection

async def audio_output_rime(transcript, voice, filetag):
    url = "https://users.rime.ai/v1/rime-tts"

    payload = {
        "speaker": voice,
        "text": transcript,
        "modelId": "mist",
        "samplingRate": SAMPLE_RATE,
        "speedAlpha": 1.3,
        "reduceLatency": False
    }
    headers = {
        "Accept": "audio/pcm",
        "Authorization": f"Bearer {API_KEYS['rime']}",
        "Content-Type": "application/json"
    }

    # Use stream=True to handle streaming response
    response = requests.request("POST", url, json=payload, headers=headers, stream=True)

    # Check if the request was successful
    if response.status_code == 200:
        with open(f"rime-{voice}-{filetag}.pcm", "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
    else:
        print("Error:", response.status_code)

async def audio_output_deepgram(transcript, voice, filetag):
    try:
        deepgram = DeepgramClient(API_KEYS['deepgram'])

        options = SpeakOptions(
            model=f"aura-{voice}-en",
            sample_rate=SAMPLE_RATE,
            encoding='linear16',
        )
        transcript = {'text': transcript}

        response = await deepgram.speak.asyncrest.v('1').save(f'deepgram-{voice}-{filetag}.wav', transcript, options)

    except Exception as e:
        print(f"Exception: {e}")

async def audio_output_elevenlabs(transcript, voice, filetag):
    client = ElevenLabs(api_key=API_KEYS['elevenlabs'])
    audio = client.text_to_speech.convert_as_stream(
        voice_id=voice[1],
        optimize_streaming_latency="0",
        output_format="pcm_16000",
        text=transcript,
        voice_settings=VoiceSettings(
            stability=0.1,
            similarity_boost=0.3,
            style=0.2,
        ),
    )
    save(audio, f"elevenlabs-{voice[0]}-{filetag}.pcm")

async def generate_alphanumeric_id(length):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def convert_pcm_to_mp3(pcm_file, sample_rate=16000, channels=1, sample_width=2):
    """Convert a PCM file to MP3 format"""
    try:
        # Create audio segment from PCM data
        audio = AudioSegment(
            data=open(pcm_file, 'rb').read(),
            sample_width=sample_width,  # 2 bytes for 16-bit audio
            frame_rate=sample_rate,
            channels=channels
        )
        
        # Create mp3 filename
        mp3_file = pcm_file.replace('.pcm', '.mp3')
        
        # Export as MP3
        audio.export(mp3_file, format='mp3')
        
        # Remove original PCM file
        os.remove(pcm_file)
        
        return True
    except Exception as e:
        print(f"Error converting {pcm_file}: {str(e)}")
        return False

async def numeric_id_test(alphanumeric_id=None):
    if not alphanumeric_id:
        alphanumeric_id = await generate_alphanumeric_id(12)
        print(f"\nGenerated ID: {alphanumeric_id}")

    for backend_name in BACKENDS:
        print(f"\n=== Processing {backend_name.upper()} ===")
        alphanumeric_id_formatted = id_formatter(alphanumeric_id, backend_name)
        transcript_phrase = "Hello, my name is Jane Smith! I'm an AI agent and assistant. How can I help you today?"
        id_phrase = "Here's an example of an alphanumeric ID. It is " + alphanumeric_id_formatted + "."
        
        for i in range(VOICES_PER_SERVICE):
            match backend_name:
                case 'cartesia':
                    print(f"Generating Cartesia audio for voice {cartesia_voices[i]['name']}...")
                    await audio_output_cartesia(transcript_phrase, cartesia_voices[i], 'intro')
                    await audio_output_cartesia(id_phrase, cartesia_voices[i], 'id')
                    # Convert PCM files to MP3
                    convert_pcm_to_mp3(f"cartesia-{cartesia_voices[i]['name']}-intro.pcm", sample_rate=8000)
                    convert_pcm_to_mp3(f"cartesia-{cartesia_voices[i]['name']}-id.pcm", sample_rate=8000)
                    print(f"✓ Completed Cartesia voice {cartesia_voices[i]['name']}")
                case 'rime':
                    print(f"Generating Rime audio for voice {rime_voices[i]}...")
                    await audio_output_rime(transcript_phrase, rime_voices[i], 'intro')
                    await audio_output_rime(id_phrase, rime_voices[i], 'id')
                    # Convert PCM files to MP3
                    convert_pcm_to_mp3(f"rime-{rime_voices[i]}-intro.pcm", sample_rate=8000)
                    convert_pcm_to_mp3(f"rime-{rime_voices[i]}-id.pcm", sample_rate=8000)
                    print(f"✓ Completed Rime voice {rime_voices[i]}")
                case 'deepgram':
                    print(f"Generating Deepgram audio for voice {deepgram_voices[i]}...")
                    await audio_output_deepgram(transcript_phrase, deepgram_voices[i], 'intro')
                    await audio_output_deepgram(id_phrase, deepgram_voices[i], 'id')
                    print(f"✓ Completed Deepgram voice {deepgram_voices[i]}")
                case 'elevenlabs':
                    print(f"Generating ElevenLabs audio for voice {elevenlabs_voices[i][0]}...")
                    await audio_output_elevenlabs(transcript_phrase, elevenlabs_voices[i], 'intro')
                    await audio_output_elevenlabs(id_phrase, elevenlabs_voices[i], 'id')
                    # Convert PCM files to MP3
                    convert_pcm_to_mp3(f"elevenlabs-{elevenlabs_voices[i][0]}-intro.pcm")
                    convert_pcm_to_mp3(f"elevenlabs-{elevenlabs_voices[i][0]}-id.pcm")
                    print(f"✓ Completed ElevenLabs voice {elevenlabs_voices[i][0]}")

async def main():
    print("Starting TTS Benchmark...")
    await numeric_id_test()
    print("\nBenchmark completed! ✨")

asyncio.run(main())