# y2t

Streamlit app that extracts text from YouTube videos.

The app first tries to read an existing YouTube transcript with
`youtube-transcript-api`. If the video does not have a usable transcript, it
downloads the audio with `yt-dlp` and transcribes it locally with OpenAI
Whisper.

## Features

- Automatic flow: try YouTube captions first, then fall back to Whisper
- Optional modes for captions-only or forced Whisper transcription
- Caption language preference controls
- Whisper model size selector
- Result tabs for transcript, timestamp chunks, and metadata
- Copy transcript button
- Transcript exports as TXT, JSON, SRT, VTT, and Markdown
- Friendlier error messages with stack traces hidden behind advanced details

## Requirements

- Python 3.10 or newer
- `ffmpeg` available on the system path
- Internet access to YouTube and to download the Whisper model on first use

On Streamlit Community Cloud, `ffmpeg` is installed through `packages.txt`.

For local macOS installs from python.org, run the bundled certificate installer
once if Whisper fails to download its model with an SSL certificate error:

```bash
"/Applications/Python 3.14/Install Certificates.command"
```

Adjust `3.14` to your installed Python version.

## Setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install Python dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Install `ffmpeg` locally if it is not already installed:

```bash
brew install ffmpeg
```

## Run

```bash
streamlit run app.py
```

Open the local URL printed by Streamlit, usually:

```text
http://localhost:8501
```

Try a sample video:

```text
https://www.youtube.com/watch?v=VXFkjxPvqfU
```

## Using the App

1. Paste a YouTube video URL.
2. Choose the transcription mode in the sidebar.
3. Choose preferred caption languages.
4. Choose a Whisper model if Whisper might be used.
5. Click **Get Transcription**.
6. Review the transcript, copy it, or export it from the transcript tab.

## Notes

- The first Whisper transcription downloads the `base` model, which is about
  139 MB. Larger Whisper models download more data and run more slowly.
- YouTube extraction can break when YouTube changes its internals. Keep
  `yt-dlp` updated when downloads or metadata extraction start failing.
- Some cloud providers may be blocked or rate limited by YouTube for transcript
  access. In those cases the app falls back to Whisper when audio download is
  still available.
