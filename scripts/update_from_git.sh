#!/bin/bash
# Update from Git and rebuild - актуализация из git

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

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "=========================================="
echo "Update from Git and Rebuild"
echo "=========================================="
echo ""

# Check if in git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    print_error "Not a git repository!"
    exit 1
fi

# Show current status
print_info "Current branch: $(git branch --show-current)"
print_info "Current commit: $(git rev-parse --short HEAD)"
echo ""

# Check for local changes
if ! git diff-index --quiet HEAD --; then
    print_warn "You have uncommitted changes:"
    git status --short
    echo ""
    read -p "Stash changes and continue? [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_step "Stashing local changes..."
        git stash push -m "Auto-stash before update $(date +%Y%m%d_%H%M%S)"
    else
        print_error "Please commit or stash your changes first"
        exit 1
    fi
fi

# Fetch updates
print_step "Fetching updates from remote..."
git fetch origin

# Show what will be updated
CURRENT_COMMIT=$(git rev-parse HEAD)
REMOTE_COMMIT=$(git rev-parse @{u} 2>/dev/null || echo "")

if [ -z "$REMOTE_COMMIT" ]; then
    print_warn "No upstream branch configured"
    read -p "Enter branch to pull from [main]: " BRANCH
    BRANCH=${BRANCH:-main}
    git branch --set-upstream-to=origin/$BRANCH
    REMOTE_COMMIT=$(git rev-parse @{u})
fi

if [ "$CURRENT_COMMIT" == "$REMOTE_COMMIT" ]; then
    print_info "Already up to date!"
    read -p "Rebuild anyway? [y/N]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
else
    print_info "Updates available:"
    git log --oneline --graph HEAD..@{u}
    echo ""
fi

# Pull updates
print_step "Pulling updates..."
if ! git pull; then
    print_error "Git pull failed! Please resolve conflicts manually."
    exit 1
fi

NEW_COMMIT=$(git rev-parse --short HEAD)
print_info "Updated to commit: $NEW_COMMIT"
echo ""

# Determine deployment type
DEPLOY_TYPE="docker"

if [ -n "$CONDA_DEFAULT_ENV" ] && [ "$CONDA_DEFAULT_ENV" == "face-recognition-system" ]; then
    print_info "Detected Conda environment"
    read -p "Update Conda environment? [Y/n]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        DEPLOY_TYPE="conda"
    fi
elif [ -f "docker-compose.yml" ]; then
    print_info "Detected Docker deployment"
    read -p "Rebuild Docker containers? [Y/n]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        print_info "Skipping rebuild"
        exit 0
    fi
fi

# Update based on deployment type
if [ "$DEPLOY_TYPE" == "conda" ]; then
    print_step "Updating Conda environment..."

    # Update environment
    conda env update -n face-recognition-system -f environment.yml --prune

    # Update pip packages
    pip install -r backend/requirements.txt --upgrade

    print_info "Conda environment updated!"
    print_warn "Please restart services manually:"
    echo "  ./scripts/stop_services.sh"
    echo "  ./scripts/start_services.sh"

elif [ "$DEPLOY_TYPE" == "docker" ]; then
    # Check for GPU
    USE_GPU=false
    if command -v nvidia-smi &> /dev/null; then
        print_info "NVIDIA GPU detected"
        read -p "Use GPU configuration? [y/N]: " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            USE_GPU=true
        fi
    fi

    # Run rebuild script
    if [ "$USE_GPU" == true ]; then
        print_step "Rebuilding with GPU support..."
        ./scripts/rebuild_containers.sh gpu
    else
        print_step "Rebuilding with CPU..."
        ./scripts/rebuild_containers.sh
    fi
fi

echo ""
print_info "=========================================="
print_info "Update completed successfully!"
print_info "=========================================="
echo ""
print_info "Changes:"
git log --oneline $CURRENT_COMMIT..HEAD | head -10
echo ""
