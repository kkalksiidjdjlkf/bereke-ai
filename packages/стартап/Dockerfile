# Wellbeing Monitoring System - Docker Image
# Produces a containerized monitoring application with all dependencies

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Audio/Video processing
    libsndfile1 \
    libsndfile1-dev \
    libportaudio2 \
    libportaudio-dev \
    # Image processing
    libopencv-dev \
    python3-opencv \
    # Required for MediaPipe
    libatlas-base-dev \
    libjasper-dev \
    libtiff5 \
    libjasper1 \
    libharfbuzz0b \
    libwebp6 \
    libtiff5 \
    libjasper1 \
    libqtgui4 \
    python3-pyqt5 \
    libqt4-test \
    libhdf5-dev \
    libharfbuzz0b \
    libwebp6 \
    libjasper1 \
    # Sound support
    pulseaudio \
    alsa-utils \
    # X11 support for visualization
    x11-apps \
    xauth \
    # Utilities
    git \
    wget \
    curl \
    nano \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements_new.txt .

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements_new.txt

# Copy application files
COPY . .

# Copy and make entrypoint script executable
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# Create directories for outputs
RUN mkdir -p /app/reports /app/data /app/exports /app/logs

# Set up volume mount points
VOLUME ["/app/reports", "/app/data", "/app/exports", "/app/logs"]

# Expose ports (for future web interface)
EXPOSE 8000 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from database import WellbeingDatabase; db = WellbeingDatabase(db_path='/app/data/wellbeing_monitor.db'); db.close(); print('OK')" || exit 1

# Set entrypoint
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Default command: show help
CMD ["help"]
