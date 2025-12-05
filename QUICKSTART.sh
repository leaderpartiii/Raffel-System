#!/bin/bash
# Быстрый старт за 5 минут для Linux/Mac

set -e

echo "🎰 RAFFLE BACKEND - БЫСТРЫЙ СТАРТ (5 минут)"
echo "=============================================="

# Проверка Python
echo "[1/5] Проверяем Python..."
python3 --version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден. Установите Python 3.9+"
    exit 1
fi

# Создаем venv
echo "[2/5] Создаем виртуальное окружение..."
python3 -m venv venv
source venv/bin/activate

# Устанавливаем зависимости
echo "[3/5] Устанавливаем зависимости..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1

# Создаем файлы
echo "[4/5] Подготавливаем конфигурацию..."
mkdir -p logs
cp .env.example .env

# Инициализируем БД
echo "[5/5] Инициализируем БД..."
python setup_db.py

echo ""
echo "✅ ГОТОВО! Следующие шаги:"
echo ""
echo "1. Отредактируйте .env файл с вашими параметрами:"
echo "   nano .env"
echo ""
echo "2. Запустите API сервер:"
echo "   python main.py api"
echo ""
echo "3. В отдельном окне терминала, запустите слушатели:"
echo "   python main.py listeners"
echo ""
echo "4. Протестируйте API:"
echo "   curl http://localhost:8000/health"
echo ""
