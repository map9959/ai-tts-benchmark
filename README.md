# AI TTS Benchmark

An open comparison between AI text-to-speech APIs

## Background

Choosing the voice for your AI agent is like choosing its "face"; it's the first impression of any user of your software. An engineer has to make sure the text-to-speech agent they use is low-latency and accurate to the LLM's output, as well as clear and natural-sounding, even over low-bitrate communications such as telephony. I had to compare vendors carefully before overhauling my company's agent to integrate one into our stack. The progress made in the field of TTS recently has been mindblowing, with new services such as Cartesia, Deepgram, Rime, and ElevenLabs taking on established tech giants as challengers with new AI-powered techniques. Rather than officially declare a winner, I want to give back to the open source and AI communities and create an easy-to-run benchmark for comparing popular text-to-speech services directly.

## Instructions

All dependencies are listed in the Pipfile, which can be installed and initialized with

```
pipenv install
```

Move `.env.example` to `.env` and fill out your API keys. It will be ignored by Git.

Run the benchmark with

```
python3 benchmark.py
```

Audiofiles in the form of `[service name]-[voice name]-[sentence type].[pcm/wav]` will be automatically generated. A script to convert all `.pcm` files to `.wav` is in progress.

## Acknowledgements

This was done as part of my backend engineering work at [**Standard Practice**](https://standardpractice.ai). If you represent a medical practice or revenue cycle management firm, and you want an AI-powered solution for making outbound calls to insurance companies, contact us!
