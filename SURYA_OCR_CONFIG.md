# Surya OCR Configuration Guide

Руководство по настройке Surya OCR для оптимальной производительности.

## Обзор

Система использует Surya OCR для извлечения текста из документов. Surya работает через предикторы (Predictors) и поддерживает GPU ускорение.

## Параметры конфигурации

### 1. DETECTOR_TEXT_THRESHOLD

**Описание:** Порог уверенности для детекции текстовых областей.

**Значение по умолчанию:** `0.2`

**Диапазон:** `0.0` - `1.0`

- **Низкие значения** (0.1-0.3): Более агрессивная детекция, больше областей считаются текстом
- **Средние значения** (0.3-0.5): Сбалансированная детекция
- **Высокие значения** (0.5-0.8): Консервативная детекция, только очевидный текст

**Когда изменять:**
- Увеличьте, если детектируется много шума как текст
- Уменьшите, если пропускаются реальные текстовые области

### 2. DETECTOR_BATCH_SIZE

**Описание:** Размер батча для детектора текстовых областей.

**Значение по умолчанию:** `8`

**Рекомендации:**
- **CPU:** 1-4
- **GPU 4GB:** 8-16
- **GPU 8GB+:** 16-32

**Влияние:**
- Больше = быстрее обработка, но больше памяти
- Меньше = медленнее, но меньше использование памяти

### 3. RECOGNITION_BATCH_SIZE

**Описание:** Размер батча для распознавания текста в детектированных областях.

**Значение по умолчанию:** `15`

**Рекомендации:**
- **CPU:** 4-8
- **GPU 4GB:** 15-30
- **GPU 8GB+:** 30-64

**Влияние:**
- Больше = быстрее распознавание текста
- Меньше = меньше использование памяти

### 4. LAYOUT_BATCH_SIZE

**Описание:** Размер батча для анализа структуры документа.

**Значение по умолчанию:** `52`

**Рекомендации:**
- **CPU:** 16-32
- **GPU 4GB:** 52-64
- **GPU 8GB+:** 64-128

### 5. PYTORCH_CUDA_ALLOC_CONF

**Описание:** Конфигурация аллокатора памяти CUDA для PyTorch.

**Значение по умолчанию:** `expandable_segments:True`

**Описание:** Позволяет PyTorch динамически расширять сегменты памяти GPU, уменьшая фрагментацию.

**Другие опции:**
- `max_split_size_mb:512` - Ограничение размера разделения блоков памяти
- `garbage_collection_threshold:0.6` - Порог для сборки мусора

## Примеры конфигураций

### Для CPU (экономия памяти)

```env
USE_GPU=false
DETECTOR_BATCH_SIZE=2
RECOGNITION_BATCH_SIZE=4
LAYOUT_BATCH_SIZE=16
DETECTOR_TEXT_THRESHOLD=0.2
```

### Для GPU 4GB (сбалансированно)

```env
USE_GPU=true
CUDA_VISIBLE_DEVICES=0
PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
DETECTOR_BATCH_SIZE=8
RECOGNITION_BATCH_SIZE=15
LAYOUT_BATCH_SIZE=52
DETECTOR_TEXT_THRESHOLD=0.2
```

### Для GPU 8GB+ (максимальная производительность)

```env
USE_GPU=true
CUDA_VISIBLE_DEVICES=0
PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
DETECTOR_BATCH_SIZE=16
RECOGNITION_BATCH_SIZE=32
LAYOUT_BATCH_SIZE=128
DETECTOR_TEXT_THRESHOLD=0.2
```

### Для высокой точности (медленнее)

```env
USE_GPU=true
DETECTOR_BATCH_SIZE=4
RECOGNITION_BATCH_SIZE=8
LAYOUT_BATCH_SIZE=32
DETECTOR_TEXT_THRESHOLD=0.15  # Более агрессивная детекция
```

## Мониторинг производительности

### Проверка использования памяти GPU

```bash
# Во время работы системы
nvidia-smi -l 1
```

### Проверка логов OCR

```bash
tail -f logs/app.log | grep "OCR"
```

Система логирует:
- Загрузку предикторов
- Время обработки каждого изображения
- Количество детектированных текстовых областей
- Ошибки и предупреждения

## Troubleshooting

### Out of Memory (OOM) errors

**Симптомы:**
```
RuntimeError: CUDA out of memory
```

**Решение:**
1. Уменьшите batch sizes:
   ```env
   DETECTOR_BATCH_SIZE=4
   RECOGNITION_BATCH_SIZE=8
   LAYOUT_BATCH_SIZE=32
   ```

2. Проверьте другие процессы на GPU:
   ```bash
   nvidia-smi
   ```

3. Установите ограничение памяти:
   ```env
   PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512,expandable_segments:True
   ```

### Медленная обработка

**Решение:**
1. Убедитесь что GPU включен:
   ```env
   USE_GPU=true
   ```

2. Увеличьте batch sizes (если позволяет память)

3. Проверьте что CUDA доступна:
   ```bash
   python -c "import torch; print(torch.cuda.is_available())"
   ```

### Пропускается текст

**Решение:**
1. Уменьшите DETECTOR_TEXT_THRESHOLD:
   ```env
   DETECTOR_TEXT_THRESHOLD=0.15
   ```

2. Проверьте качество изображения (минимум 300 DPI для документов)

### Много ложных срабатываний

**Решение:**
1. Увеличьте DETECTOR_TEXT_THRESHOLD:
   ```env
   DETECTOR_TEXT_THRESHOLD=0.3
   ```

## API использование

### Python код

```python
from app.services.ocr_service import ocr_service
from PIL import Image

# Загрузить изображение
image = Image.open("document.jpg")

# Извлечь текст
result = ocr_service.extract_text_from_image("document.jpg")

if result["success"]:
    print(f"Text: {result['full_text']}")
    print(f"Confidence: {result['confidence_score']}")
    print(f"Time: {result['processing_time_seconds']}s")
else:
    print(f"Error: {result['error']}")
```

### Прямое использование Surya API

```python
from PIL import Image
from surya.foundation import FoundationPredictor
from surya.detection import DetectionPredictor
from surya.recognition import RecognitionPredictor

# Инициализация предикторов
foundation_predictor = FoundationPredictor()
detection_predictor = DetectionPredictor()
recognition_predictor = RecognitionPredictor(foundation_predictor)

# Загрузка изображения
image = Image.open("document.jpg")

# OCR
predictions = recognition_predictor([image], det_predictor=detection_predictor)

# Обработка результатов
for prediction in predictions:
    for text_line in prediction.text_lines:
        print(text_line.text)
```

### REST API

```bash
# Upload and process document
curl -X POST http://localhost:30000/api/v1/documents/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.pdf"
```

## Архитектура

```
                 FoundationPredictor
                        ↓
Image → DetectionPredictor → Text Regions
                ↓
         RecognitionPredictor → Text Lines
                ↓
         Confidence Calculation → Final Result
```

### FoundationPredictor

- Базовая модель-основа для всех предикторов
- Предоставляет общие компоненты и веса
- Инициализируется первым и передается в RecognitionPredictor

### DetectionPredictor

- Находит области с текстом на изображении
- Использует модель на основе трансформеров
- Возвращает bounding boxes для найденных текстовых регионов

### RecognitionPredictor

- Требует FoundationPredictor для инициализации
- Распознает текст в найденных областях (использует DetectionPredictor)
- Поддерживает 90+ языков
- Возвращает текст и confidence scores

## Best Practices

1. **Запускайте проверку зависимостей:**
   ```bash
   cd backend
   python scripts/check_dependencies.py
   ```

2. **Мониторьте логи при первом запуске:**
   ```bash
   tail -f logs/app.log
   ```

3. **Настройте batch sizes под ваше оборудование**

4. **Используйте GPU для production окружения**

5. **Регулярно проверяйте nvidia-smi при использовании GPU**

## Дополнительные ресурсы

- [Surya OCR GitHub](https://github.com/VikParuchuri/surya)
- [PyTorch CUDA Memory Management](https://pytorch.org/docs/stable/notes/cuda.html)
- [Project README](./README.md)
- [Environment Configuration](./ENV_CONFIGURATION.md)
