#!/bin/bash
# Setup script for Conda environment deployment
# Автоматическое развертывание на локальной машине через Conda

set -e  # Exit on error

echo "=========================================="
echo "Face Recognition & OCR System - Conda Setup"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if conda is installed
if ! command -v conda &> /dev/null; then
    print_error "Conda is not installed!"
    echo "Please install Anaconda or Miniconda first:"
    echo "https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

print_info "Conda found: $(conda --version)"

# Detect GPU availability
if command -v nvidia-smi &> /dev/null; then
    print_info "NVIDIA GPU detected:"
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
    USE_GPU=true
else
    print_warn "No NVIDIA GPU detected - will use CPU-only version"
    USE_GPU=false
fi

# Ask user preference
echo ""
read -p "Do you want to set up GPU acceleration (requires NVIDIA GPU)? [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ "$USE_GPU" = false ]; then
        print_warn "GPU acceleration requested but no GPU detected. Continuing anyway..."
    fi
    SETUP_GPU=true
    ENV_FILE="environment-gpu.yml"
else
    SETUP_GPU=false
    ENV_FILE="environment.yml"
fi

print_info "Using environment file: ${ENV_FILE}"

# Create or update conda environment
ENV_NAME="face-recognition-system"

if conda env list | grep -q "^${ENV_NAME} "; then
    print_warn "Environment '${ENV_NAME}' already exists"
    read -p "Do you want to remove and recreate it? [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Removing existing environment..."
        conda env remove -n ${ENV_NAME} -y
    else
        print_info "Updating existing environment..."
        conda env update -n ${ENV_NAME} -f ${ENV_FILE}
        print_info "Environment updated!"
        exit 0
    fi
fi

# Create new environment
print_info "Creating conda environment from ${ENV_FILE}..."
conda env create -f ${ENV_FILE}

# Activate environment
print_info "Activating environment..."
eval "$(conda shell.bash hook)"
conda activate ${ENV_NAME}

# Verify GPU installation if GPU was set up
if [ "$SETUP_GPU" = true ]; then
    print_info "Verifying GPU installation..."
    python -c "import torch; print(f'PyTorch CUDA available: {torch.cuda.is_available()}')" || print_warn "CUDA verification failed"
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    print_info "Creating .env file from template..."
    cp .env.example .env

    if [ "$SETUP_GPU" = true ]; then
        echo "USE_GPU=true" >> .env
        print_info "Added USE_GPU=true to .env"
    fi

    print_warn "Please edit .env and set your SECRET_KEY and other configuration"
fi

# Create necessary directories
print_info "Creating data directories..."
mkdir -p data/uploads data/db data/cache logs models

# Check if Redis is running
print_info "Checking for Redis..."
if ! pgrep -x redis-server > /dev/null; then
    print_warn "Redis is not running!"
    echo "You need to start Redis. Options:"
    echo "  1. Using Docker: docker run -d -p 6379:6379 redis:7-alpine"
    echo "  2. Using system package: sudo systemctl start redis"
    echo "  3. Using conda: conda install -c conda-forge redis && redis-server &"
fi

# Check if Elasticsearch is running
print_info "Checking for Elasticsearch..."
if ! curl -s http://localhost:9200 > /dev/null 2>&1; then
    print_warn "Elasticsearch is not running!"
    echo "You need to start Elasticsearch. Options:"
    echo "  1. Using Docker:"
    echo "     docker run -d -p 9200:9200 -p 9300:9300 \\"
    echo "       -e \"discovery.type=single-node\" \\"
    echo "       -e \"xpack.security.enabled=false\" \\"
    echo "       docker.elastic.co/elasticsearch/elasticsearch:8.10.0"
fi

echo ""
print_info "=========================================="
print_info "Setup completed successfully!"
print_info "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Activate the environment:"
echo "   conda activate ${ENV_NAME}"
echo ""
echo "2. Make sure Redis and Elasticsearch are running (see warnings above)"
echo ""
echo "3. Initialize the database:"
echo "   python scripts/init_db.py"
echo "   python scripts/init_elasticsearch.py"
echo ""
echo "4. Create admin user:"
echo "   python scripts/create_admin.py --username admin --password <your-password>"
echo ""
echo "5. Start the backend:"
echo "   cd backend && uvicorn app.main:app --reload"
echo ""
echo "6. In a new terminal, start Celery worker:"
echo "   conda activate ${ENV_NAME}"
echo "   cd backend"
echo "   celery -A app.celery_app worker --loglevel=info"
echo ""
echo "7. In another terminal, start frontend:"
echo "   cd frontend && npm install && npm run dev"
echo ""
echo "8. Open http://localhost:3003 in your browser"
echo ""

if [ "$SETUP_GPU" = true ]; then
    echo "GPU acceleration is ENABLED"
    echo "Verify with: python -c 'import torch; print(torch.cuda.is_available())'"
    echo ""
fi

print_info "For more information, see README.md"
