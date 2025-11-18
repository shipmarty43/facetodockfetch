#!/bin/bash
# Fix PyTorch and torchvision compatibility issues
# This script reinstalls PyTorch with compatible versions

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

echo "=========================================="
echo "Fix PyTorch and torchvision compatibility"
echo "=========================================="
echo ""

# Check if conda environment is activated
if [[ "$CONDA_DEFAULT_ENV" != "face-recognition-system" ]]; then
    print_error "Conda environment not activated!"
    echo "Please run: conda activate face-recognition-system"
    exit 1
fi

print_info "Current environment: $CONDA_DEFAULT_ENV"
echo ""

# Check current versions
print_step "Checking current versions..."
python -c "import torch; print(f'PyTorch: {torch.__version__}')" 2>/dev/null || echo "PyTorch: not installed"
python -c "import torchvision; print(f'torchvision: {torchvision.__version__}')" 2>/dev/null || echo "torchvision: not installed"
echo ""

# Ask for confirmation
print_warn "This will reinstall PyTorch and torchvision with compatible versions"
print_info "Target versions: PyTorch 2.1.2, torchvision 0.16.2, CUDA 11.8"
echo ""
read -p "Continue? [y/N]: " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_info "Cancelled"
    exit 0
fi

# Uninstall old versions
print_step "Uninstalling old versions..."
pip uninstall -y torch torchvision torchaudio 2>/dev/null || true
conda remove -y pytorch torchvision pytorch-cuda 2>/dev/null || true
print_info "✓ Old versions removed"
echo ""

# Install compatible versions
print_step "Installing PyTorch 2.1.2 with CUDA 11.8 support..."
conda install -y pytorch=2.1.2 torchvision=0.16.2 pytorch-cuda=11.8 -c pytorch -c nvidia

if [ $? -eq 0 ]; then
    print_info "✓ PyTorch and torchvision installed successfully"
else
    print_error "Failed to install PyTorch"
    exit 1
fi
echo ""

# Verify installation
print_step "Verifying installation..."
python -c "import torch; print(f'✓ PyTorch: {torch.__version__}')"
python -c "import torchvision; print(f'✓ torchvision: {torchvision.__version__}')"

# Check CUDA availability
echo ""
print_step "Checking CUDA availability..."
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'CUDA version: {torch.version.cuda if torch.cuda.is_available() else \"N/A\"}')"

if python -c "import torch; exit(0 if torch.cuda.is_available() else 1)" 2>/dev/null; then
    python -c "import torch; print(f'GPU device: {torch.cuda.get_device_name(0)}')"
    print_info "✓ GPU is available and working"
else
    print_warn "⚠ CUDA not available (CPU mode will be used)"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}Fix completed successfully!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo -e "  1. Restart your services: ${GREEN}./scripts/start_services.sh${NC}"
echo -e "  2. Test OCR: ${BLUE}curl http://localhost:30000/health${NC}"
echo ""
