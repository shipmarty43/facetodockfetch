# GPU Troubleshooting Guide - NVIDIA Container Runtime

## Проблема

```
nvidia-container-cli: initialization error: load library failed:
libnvidia-ml.so.1: cannot open shared object file: no such file or directory
```

Эта ошибка означает, что NVIDIA драйверы не доступны для Docker контейнера.

---

## Быстрая диагностика

Выполните эти команды на сервере:

```bash
# 1. Проверить NVIDIA драйверы
nvidia-smi

# 2. Проверить загружены ли модули NVIDIA
lsmod | grep nvidia

# 3. Проверить установку nvidia-container-toolkit
dpkg -l | grep nvidia-container

# 4. Проверить библиотеки NVIDIA
ldconfig -p | grep nvidia

# 5. Проверить Docker runtime конфигурацию
docker info | grep -i runtime
```

---

## Решение 1: Установка NVIDIA драйверов (если не установлены)

### Проверка наличия GPU

```bash
lspci | grep -i nvidia
```

Если команда ничего не выводит - у вас нет NVIDIA GPU.

### Установка драйверов (Ubuntu/Debian)

```bash
# Обновить систему
sudo apt-get update
sudo apt-get upgrade -y

# Установить рекомендуемый драйвер
sudo ubuntu-drivers autoinstall

# Или установить конкретную версию
sudo apt-get install -y nvidia-driver-535

# Перезагрузить систему
sudo reboot
```

После перезагрузки проверьте:

```bash
nvidia-smi
```

Должна появиться информация о GPU.

---

## Решение 2: Установка nvidia-container-toolkit

```bash
# Добавить GPG ключ
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
  sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

# Добавить репозиторий
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# Установить пакеты
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit nvidia-container-runtime

# Настроить Docker для использования NVIDIA runtime
sudo nvidia-ctk runtime configure --runtime=docker

# Перезапустить Docker
sudo systemctl restart docker
```

### Проверка установки

```bash
# Проверить что nvidia-container-toolkit установлен
dpkg -l | grep nvidia-container

# Должно показать:
# nvidia-container-toolkit
# nvidia-container-toolkit-base
# libnvidia-container-tools
# libnvidia-container1
```

---

## Решение 3: Настройка Docker daemon

Создайте или обновите `/etc/docker/daemon.json`:

```bash
sudo tee /etc/docker/daemon.json > /dev/null <<'EOF'
{
  "runtimes": {
    "nvidia": {
      "path": "nvidia-container-runtime",
      "runtimeArgs": []
    }
  },
  "default-runtime": "nvidia"
}
EOF

# Перезапустить Docker
sudo systemctl restart docker
```

---

## Решение 4: Ручная загрузка модулей NVIDIA

Если `nvidia-smi` не работает после установки драйверов:

```bash
# Загрузить модули
sudo modprobe nvidia
sudo modprobe nvidia_uvm

# Проверить загрузку
lsmod | grep nvidia

# Если модули загружены, попробуйте nvidia-smi
nvidia-smi
```

---

## Тестирование GPU в Docker

После настройки протестируйте:

```bash
# Тест 1: Простой CUDA контейнер
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# Тест 2: Проверка всех GPU
docker run --rm --gpus all ubuntu nvidia-smi

# Тест 3: Использование конкретного GPU
docker run --rm --gpus '"device=0"' nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

Если тесты проходят успешно, GPU готов для использования!

---

## Запуск проекта с GPU

После успешной настройки:

```bash
cd /home/admin1/facetodockfetch

# Пересобрать GPU версию
docker-compose -f docker-compose.gpu.yml build

# Запустить
docker-compose -f docker-compose.gpu.yml up -d

# Проверить логи
docker-compose -f docker-compose.gpu.yml logs backend | grep CUDA
docker-compose -f docker-compose.gpu.yml logs backend | grep GPU
```

---

## Временное решение: Использовать CPU версию

Пока настраиваете GPU, можете использовать CPU версию:

```bash
cd /home/admin1/facetodockfetch

# Остановить GPU версию
docker-compose -f docker-compose.gpu.yml down

# Запустить CPU версию
docker-compose up -d

# Проверить статус
docker-compose ps

# Просмотреть логи
docker-compose logs -f backend
```

**Особенности CPU версии:**
- ✅ Работает без GPU/NVIDIA драйверов
- ✅ Все функции доступны
- ✅ Быстрая установка
- ⚠️ Медленнее обработка (10-50x)
- ✅ Подходит для разработки и тестирования

---

## Диагностический скрипт

Сохраните и запустите этот скрипт для полной диагностики:

```bash
#!/bin/bash
# GPU Diagnostic Script

echo "=== System Information ==="
uname -a
cat /etc/os-release | grep PRETTY_NAME

echo -e "\n=== GPU Hardware ==="
lspci | grep -i nvidia || echo "No NVIDIA GPU found"

echo -e "\n=== NVIDIA Driver ==="
nvidia-smi 2>&1 || echo "nvidia-smi failed"

echo -e "\n=== NVIDIA Kernel Modules ==="
lsmod | grep nvidia || echo "No NVIDIA modules loaded"

echo -e "\n=== NVIDIA Libraries ==="
ldconfig -p | grep nvidia | head -10

echo -e "\n=== Docker Version ==="
docker --version

echo -e "\n=== Docker Runtime Configuration ==="
cat /etc/docker/daemon.json 2>/dev/null || echo "No daemon.json"

echo -e "\n=== Docker Info - Runtime ==="
docker info 2>/dev/null | grep -i runtime

echo -e "\n=== NVIDIA Container Toolkit ==="
dpkg -l | grep nvidia-container || echo "nvidia-container-toolkit not installed"

echo -e "\n=== nvidia-container-runtime ==="
which nvidia-container-runtime || echo "nvidia-container-runtime not found"

echo -e "\n=== Test Docker GPU Access ==="
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi 2>&1 | head -20
```

Сохраните как `gpu_diagnostic.sh`, сделайте исполняемым и запустите:

```bash
chmod +x gpu_diagnostic.sh
./gpu_diagnostic.sh > gpu_diagnostic.log 2>&1
cat gpu_diagnostic.log
```

---

## Частые проблемы и решения

### Проблема: "nvidia-smi: command not found"
**Решение:** NVIDIA драйверы не установлены. См. "Решение 1" выше.

### Проблема: "NVIDIA-SMI has failed because it couldn't communicate with the NVIDIA driver"
**Решение:**
1. Перезагрузите систему: `sudo reboot`
2. Проверьте модули: `sudo modprobe nvidia`
3. Переустановите драйвер

### Проблема: "docker: Error response from daemon: could not select device driver"
**Решение:** nvidia-container-toolkit не установлен. См. "Решение 2" выше.

### Проблема: "No NVIDIA GPU detected in docker container"
**Решение:** Docker не настроен для GPU. См. "Решение 3" выше.

### Проблема: У меня нет NVIDIA GPU на сервере
**Решение:** Используйте CPU версию проекта:
```bash
docker-compose up -d  # Вместо docker-compose.gpu.yml
```

---

## Проверка после исправления

```bash
# 1. nvidia-smi должен работать
nvidia-smi

# 2. Docker GPU тест должен пройти
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# 3. Проект должен запуститься
cd /home/admin1/facetodockfetch
docker-compose -f docker-compose.gpu.yml up -d

# 4. Backend должен видеть CUDA
docker-compose -f docker-compose.gpu.yml exec backend python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

Все 4 проверки должны пройти успешно!

---

## Контакты для помощи

Если проблема не решается:

1. Запустите диагностический скрипт выше
2. Сохраните вывод
3. Проверьте документацию NVIDIA: https://docs.nvidia.com/datacenter/cloud-native/
4. Используйте CPU версию как временное решение

---

## Дополнительные ресурсы

- [NVIDIA Container Toolkit Installation Guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
- [Docker GPU Support](https://docs.docker.com/config/containers/resource_constraints/#gpu)
- [NVIDIA Driver Download](https://www.nvidia.com/download/index.aspx)
