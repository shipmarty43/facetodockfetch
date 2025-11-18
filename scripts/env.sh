#!/bin/bash
# Environment variables for Face Recognition System
# Source this file in your scripts or shell: source scripts/env.sh

# Suppress bcrypt version warnings from passlib
# bcrypt 4.0+ changed internal structure but passlib works correctly
export PYTHONWARNINGS="ignore::UserWarning:passlib"

# Optional: Set CUDA device visibility
# export CUDA_VISIBLE_DEVICES=0

# Optional: PyTorch CUDA memory allocator configuration
# export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"

echo "Environment variables set for Face Recognition System"
