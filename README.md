# Crystal-voice-AI
# 💎 Crystal Voice AI

An AI-powered speech-to-text app — record from your mic or upload an audio
file, and get an instant transcript.

## Setup

1. **Install FFmpeg** (required by Whisper to read audio):
   - Windows: `winget install ffmpeg` (or download from ffmpeg.org and add to PATH)
   - Mac: `brew install ffmpeg`
   - Linux: `sudo apt install ffmpeg`

   **Important (Windows):** after installing, fully close and reopen your
   terminal / PowerShell / VS Code so it picks up the updated PATH. Verify
   it worked by running `ffmpeg -version` in the **new** terminal window —
   if that command isn't recognized, the app won't be able to transcribe
   audio either. The app's sidebar will also show whether FFmpeg was
   detected.

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the app:**
   ```bash
   streamlit run app.py
   ```

## Notes

- The first transcription will take longer since the Whisper model needs to
  download (`tiny` ≈ 75MB, `base` ≈ 145MB, `small` ≈ 490MB, `medium` ≈ 1.5GB).
- Choose a smaller model (`tiny`/`base`) for speed, or `small`/`medium` for
  better accuracy on longer or noisy recordings — from the sidebar.
- Mic recording requires the browser to have microphone permission enabled
  for the page.
- Supported upload formats: MP3, WAV, M4A, OGG, FLAC, WEBM.
