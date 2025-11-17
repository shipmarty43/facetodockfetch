# Testing Suite

Automated tests for Face Recognition & OCR System.

## Test Structure

```
tests/
├── __init__.py           # Test package init
├── test_imports.py       # Package import tests
├── test_api.py          # FastAPI endpoint tests
└── README.md            # This file
```

## Running Tests

### Quick Environment Test

Fast validation of conda environment and core packages:

```bash
# Run environment test (5-10 seconds)
python scripts/test_environment.py

# Skip slow model loading
python scripts/test_environment.py --skip-model
```

**Output:**
- ✓ Core package imports (13 packages)
- ✓ OpenCV functionality
- ✓ Application modules
- ✓ FastAPI initialization
- ✓ GPU availability
- ✓ InsightFace model (optional, can be slow)

### Advanced Environment Test with Logging

Comprehensive testing with detailed logs and reports:

```bash
# Run with advanced logging
python scripts/test_environment_advanced.py
```

**Features:**
- 📝 **Text logs** with timestamps: `logs/test_environment_YYYYMMDD_HHMMSS.log`
- 📊 **JSON reports** for CI/CD: `logs/test_environment_YYYYMMDD_HHMMSS.json`
- 📈 **HTML dashboard** with charts: `logs/test_environment_YYYYMMDD_HHMMSS.html`
- ⏱️ **Performance metrics** for each test
- 💻 **System information** (CPU, GPU, CUDA)
- 📉 **Pass/fail statistics** with percentages

**JSON Output Example:**
```json
{
  "system_info": {
    "platform": "Linux-4.4.0-x86_64",
    "python_version": "3.11.9",
    "cuda_available": true,
    "gpu_name": "NVIDIA RTX 3080"
  },
  "summary": {
    "total_tests": 13,
    "passed": 13,
    "failed": 0,
    "pass_rate": 100.0,
    "total_duration": 8.45
  }
}
```

**HTML Report Includes:**
- Color-coded test results table
- System information panel
- Pass/fail statistics with visual indicators
- Detailed error messages
- Performance timing for each test

### Full Pytest Suite

Comprehensive unit and integration tests:

```bash
# Activate environment
conda activate face-recognition-system

# Run all tests
pytest

# Run specific test file
pytest tests/test_imports.py

# Run specific test class
pytest tests/test_api.py::TestHealthCheck

# Run with coverage
pytest --cov=backend/app --cov-report=html
```

### Test Categories

```bash
# Unit tests only (fast)
pytest -m unit

# Skip slow tests
pytest -m "not slow"

# GPU tests only
pytest -m gpu
```

## Test Coverage

### test_imports.py

**Core Package Tests:**
- FastAPI, PyTorch, OpenCV, NumPy, Pillow
- SQLAlchemy, Celery, Redis, Elasticsearch
- Pydantic, ONNX Runtime

**ML Package Tests:**
- InsightFace, MRZ, Surya OCR

**Application Module Tests:**
- Configuration, Database models
- Face recognition service
- OCR service
- Elasticsearch service

**Functionality Tests:**
- OpenCV image operations
- PyTorch tensor operations
- MRZ parsing (TD1, TD3)

### test_api.py

**Health Check Tests:**
- `/health` endpoint
- Root `/` endpoint

**API Route Tests:**
- Route registration
- OpenAPI schema generation

**Endpoint Tests:**
- Authentication (login, register)
- Document upload and listing
- Face and text search
- CORS configuration
- Error handling (404, validation)

## CI/CD Integration

### GitHub Actions

```yaml
- name: Run tests
  run: |
    conda activate face-recognition-system
    pytest --junitxml=test-results.xml
```

### Docker

```bash
# Run tests in Docker
docker-compose exec backend pytest

# Run with coverage
docker-compose exec backend pytest --cov=app
```

## Writing New Tests

### Test Structure

```python
import pytest

class TestFeature:
    """Test feature description"""

    def test_specific_behavior(self):
        """Test specific behavior"""
        # Arrange
        input_data = ...

        # Act
        result = function_under_test(input_data)

        # Assert
        assert result == expected_value
```

### Fixtures

```python
@pytest.fixture
def sample_image():
    """Provide sample image for tests"""
    import numpy as np
    return np.zeros((100, 100, 3), dtype=np.uint8)

def test_with_fixture(sample_image):
    assert sample_image.shape == (100, 100, 3)
```

### Markers

```python
@pytest.mark.slow
def test_slow_operation():
    """This test takes a long time"""
    pass

@pytest.mark.gpu
def test_gpu_operation():
    """This test requires GPU"""
    import torch
    assert torch.cuda.is_available()
```

## Troubleshooting

### Import Errors

If tests fail with import errors:

```bash
# Ensure environment is activated
conda activate face-recognition-system

# Verify packages are installed
python scripts/test_environment.py
```

### Database Tests

For tests requiring database:

```bash
# Set test database
export DATABASE_URL="sqlite:///./test.db"

# Or use pytest-env plugin
pip install pytest-env
```

### External Services

For tests requiring Redis/Elasticsearch:

```bash
# Start services
docker-compose up -d redis elasticsearch

# Or mock them in tests
pytest tests/ --mock-services
```

## Performance

| Test Suite | Duration | Tests |
|------------|----------|-------|
| test_imports.py | ~5s | 25 |
| test_api.py | ~2s | 15 |
| Environment test | ~10s | 6 |
| **Total** | **~17s** | **46** |

*InsightFace model loading adds ~60s if not skipped*

## Best Practices

1. **Fast Tests First** - Keep unit tests fast (<1s each)
2. **Isolate Tests** - Each test should be independent
3. **Mock External Services** - Don't rely on Redis/ES for unit tests
4. **Clear Names** - Test names should describe what they test
5. **Arrange-Act-Assert** - Use AAA pattern for clarity

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)
