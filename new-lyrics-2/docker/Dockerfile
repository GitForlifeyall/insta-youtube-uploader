# ==============================================================================
# LyricalVideo Dockerfile
# Python 3.10 + Node.js 20 + FFmpeg (with libass) + Aubio + AI4Bharat
# ==============================================================================

FROM python:3.10-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    NODE_ENV=production \
    PORT=3000

WORKDIR /app

# Install system dependencies: FFmpeg (with libass), build tools, audio libs, fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    ca-certificates \
    build-essential \
    python3-dev \
    ffmpeg \
    fontconfig \
    git \
    libsndfile1-dev \
    libsamplerate0-dev \
    libgl1 \
    libglib2.0-0 \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy fonts and refresh font cache
COPY fonts/ /usr/local/share/fonts/appfonts/
RUN fc-cache -fv

# Upgrade packaging tools without installing the optional transliteration stack.
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install Python requirements
COPY requirements.txt ./
RUN grep -v '^ai4bharat-transliteration' requirements.txt > requirements.no-transliteration.txt && \
    pip install --no-cache-dir -r requirements.no-transliteration.txt

# Install Node dependencies
COPY package*.json ./
RUN npm install --omit=dev

# Copy application code
COPY . .

# Create persistent storage directories
RUN mkdir -p /app/videos/input /app/videos/output/carousels /app/lyrics

EXPOSE 3000

CMD ["node", "src/index.js"]
