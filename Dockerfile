FROM python:3.10-slim

# Install system dependencies including FFmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download Whisper tiny model into image so runtime has 0s delay!
RUN python -c "from faster_whisper import WhisperModel; WhisperModel('tiny', device='cpu', compute_type='int8')"

# Copy application files
COPY . /app/

# Port 7860 is standard for Hugging Face Spaces & Render PORT
EXPOSE 7860
EXPOSE 8000

ENV PORT=7860

CMD ["sh", "-c", "python server.py --port ${PORT:-7860}"]
