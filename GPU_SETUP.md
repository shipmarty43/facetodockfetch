# GPU Setup Guide

Руководство по настройке CUDA/GPU для ускорения обработки лиц.

## Системные требования

### GPU
- NVIDIA GPU с CUDA Compute Capability 3.5+ (рекомендуется 7.0+)
- Минимум 4GB VRAM (рекомендуется 8GB+)
- Поддерживаемые карты:
  - RTX 30xx/40xx серии (идеально)
  - GTX 16xx серии
  - RTX 20xx серии
  - Quadro серии

### Драйверы
- NVIDIA Driver: 450.80.02 или новее
- CUDA Toolkit: 11.8 (автоматически в Docker)

## Проверка GPU

```bash
# Проверить наличие GPU
nvidia-smi

# Должен показать информацию о GPU, например:
# | NVIDIA GeForce RTX 3080    | 00000000:01:00.0 | 10GB |
```

## Вариант 1: Docker Compose с GPU

### Установка NVIDIA Container Toolkit

```bash
# Ubuntu/Debian
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker

# Проверка
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### Запуск с GPU

```bash
# Использовать GPU версию docker-compose
docker-compose -f docker-compose.gpu.yml up -d

# Проверить что GPU используется
docker-compose -f docker-compose.gpu.yml exec backend python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"

# Должно вывести: CUDA available: True
```

### Инициализация

```bash
# То же самое, но с GPU compose файлом
docker-compose -f docker-compose.gpu.yml exec backend python scripts/init_db.py
docker-compose -f docker-compose.gpu.yml exec backend python scripts/init_elasticsearch.py
docker-compose -f docker-compose.gpu.yml exec backend python scripts/create_admin.py --username admin --password admin123
```

## Вариант 2: Conda с GPU

### Установка CUDA

```bash
# Установить CUDA toolkit через conda
conda install -c conda-forge cudatoolkit=11.8

# Или системный CUDA (Ubuntu)
wget https://developer.download.nvidia.com/compute/cuda/11.8.0/local_installers/cuda_11.8.0_520.61.05_linux.run
sudo sh cuda_11.8.0_520.61.05_linux.run
```

### Установка Python пакетов

```bash
# Активировать окружение
conda activate face-recognition-system

# Установить PyTorch с CUDA
pip install torch==2.0.1+cu118 torchvision==0.15.2+cu118 \
  --extra-index-url https://download.pytorch.org/whl/cu118

# Установить ONNX Runtime GPU
pip install onnxruntime-gpu==1.16.3

# Проверка
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
python -c "import torch; print(f'GPU: {torch.cuda.get_device_name(0)}')"
```

### Настройка .env

```bash
# Добавить в .env
echo "USE_GPU=true" >> .env
```

### Запуск

```bash
# Использовать скрипт setup с GPU
./scripts/setup_conda.sh
# Выбрать "Yes" когда спросит про GPU

# Запустить сервисы
./scripts/start_services.sh
```

## Проверка GPU работы

### Health Check

```bash
# Проверить через API
curl http://localhost:8000/health

# Ответ должен содержать:
# {
#   "status": "healthy",
#   "gpu": "available (NVIDIA GeForce RTX 3080)",
#   ...
# }
```

### Логи

```bash
# Docker
docker-compose -f docker-compose.gpu.yml logs backend | grep -i cuda
docker-compose -f docker-compose.gpu.yml logs backend | grep -i gpu

# Conda
tail -f logs/backend.log | grep -i cuda

# Должно быть:
# CUDA is available! GPU: NVIDIA GeForce RTX 3080
# GPU acceleration ENABLED
# InsightFace model loaded successfully with providers: ['CUDAExecutionProvider', 'CPUExecutionProvider']
```

## Производительность

### Ожидаемое ускорение

| Операция | CPU (Ryzen 9) | GPU (RTX 3080) | Ускорение |
|----------|---------------|----------------|-----------|
| Face detection | 0.5s | 0.08s | ~6x |
| Face embedding | 0.5s | 0.05s | ~10x |
| Batch (100 faces) | 50s | 5s | ~10x |
| OCR (Surya) | 5s | 3s | ~1.7x |

### Тестирование производительности

```python
# Тест через Python
import time
from backend.app.services.face_recognition import face_recognition_service

# Загрузить тестовое изображение
image_path = "test_image.jpg"

# Тест без batch
start = time.time()
faces = face_recognition_service.detect_faces(image_path)
elapsed = time.time() - start
print(f"Single image: {elapsed:.3f}s, detected {len(faces)} faces")

# Batch тест
import glob
images = glob.glob("test_images/*.jpg")[:100]

start = time.time()
for img in images:
    faces = face_recognition_service.detect_faces(img)
elapsed = time.time() - start

print(f"Batch (100 images): {elapsed:.3f}s")
print(f"Average per image: {elapsed/100:.3f}s")
```

## Мониторинг GPU

### Real-time мониторинг

```bash
# Смотреть использование GPU в реальном времени
watch -n 1 nvidia-smi

# Или более детально
nvidia-smi dmon -s pucvmet
```

### Логи GPU использования

```bash
# Логировать в файл
nvidia-smi --query-gpu=timestamp,name,utilization.gpu,utilization.memory,memory.used,memory.total \
  --format=csv -l 1 > gpu_usage.log
```

## Troubleshooting

### CUDA not available

```bash
# Проверить что драйвер установлен
nvidia-smi

# Проверить CUDA в Docker
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# Проверить что PyTorch видит CUDA
python -c "import torch; print(torch.version.cuda)"
```

### Out of Memory (OOM)

Если получаете ошибки нехватки памяти:

```bash
# В .env уменьшить batch size
BATCH_SIZE=16  # было 32

# Уменьшить размер detection
FACE_DETECTION_SIZE=480  # было 640

# Уменьшить concurrency в Celery
# В docker-compose.gpu.yml:
command: celery -A app.celery_app worker --loglevel=info --concurrency=4  # было 8
```

### Медленная работа с GPU

```bash
# Убедиться что используется GPU, а не CPU
docker-compose -f docker-compose.gpu.yml logs backend | grep -i provider

# Должно быть CUDAExecutionProvider, а не CPUExecutionProvider
```

### Mixed GPU/CPU

Если хотите использовать GPU только для некоторых задач:

```python
# В .env
USE_GPU=true  # Общий флаг

# В коде можно переопределить для конкретных сервисов
# backend/app/services/face_recognition.py
# Изменить логику _load_model() под свои нужды
```

## Рекомендации

### Для разработки
- Используйте CPU версию (быстрее собирается Docker, меньше ресурсов)
- GPU нужен только для production нагрузки

### Для production
- Всегда используйте GPU версию
- Мониторьте температуру GPU
- Настройте автоматический restart при OOM

### Оптимальные настройки

Для RTX 3080 (10GB VRAM):
```env
BATCH_SIZE=32
CELERY_WORKERS=8
FACE_DETECTION_SIZE=640
```

Для GTX 1660 (6GB VRAM):
```env
BATCH_SIZE=16
CELERY_WORKERS=4
FACE_DETECTION_SIZE=480
```

## Дополнительные ресурсы

- [NVIDIA CUDA Installation Guide](https://docs.nvidia.com/cuda/cuda-installation-guide-linux/index.html)
- [PyTorch CUDA Documentation](https://pytorch.org/docs/stable/cuda.html)
- [ONNX Runtime GPU](https://onnxruntime.ai/docs/execution-providers/CUDA-ExecutionProvider.html)
- [InsightFace GPU Setup](https://github.com/deepinsight/insightface/tree/master/python-package)
