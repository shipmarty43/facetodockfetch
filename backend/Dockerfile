# Backend Dockerfile - Conda version
FROM continuumio/miniconda3:latest

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpoppler-cpp-dev \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libssl-dev \
    libffi-dev \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Configure conda to avoid channel priority issues
RUN conda config --set channel_priority flexible

# Accept Anaconda Terms of Service
RUN conda config --set allow_conda_downgrades true && \
    echo "yes" | conda tos accept

# Set working directory
WORKDIR /app

# Copy environment file
COPY environment.yml .

# Create conda environment
RUN conda env create -f environment.yml && \
    conda clean -afy

# Activate environment
SHELL ["conda", "run", "-n", "face-recognition-system", "/bin/bash", "-c"]

# Reinstall cryptography from source to ensure OpenSSL compatibility
RUN pip install --no-cache-dir --force-reinstall --no-binary cryptography cryptography

# Verify installation
RUN python -c "import torch; import fastapi; import insightface; print('Conda environment OK')"

# Copy application code
COPY backend/app ./app

# Create necessary directories
RUN mkdir -p data/uploads data/db data/cache logs models

# Expose port
EXPOSE 30000

# Run application with conda environment
CMD ["conda", "run", "--no-capture-output", "-n", "face-recognition-system", \
     "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "30000"]
