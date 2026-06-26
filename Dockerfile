FROM python:3.11-slim-bookworm

# Install Chrome — let the .deb handle its own deps to avoid Debian version drift
RUN apt-get update && apt-get install -y \
    wget gnupg curl unzip \
    --no-install-recommends && \
    wget -q -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt-get install -y /tmp/chrome.deb && \
    rm /tmp/chrome.deb && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Environment
ENV PYTHONUNBUFFERED=1
ENV HEADLESS=true
ENV CHROME_BIN=/usr/bin/google-chrome

EXPOSE 8000

CMD ["uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8000"]
