#!/bin/bash

# Setup script for Raffle Backend

echo "🎰 Setting up Raffle Backend..."

# Проверяем Python версию
python_version=$(python3 --version 2>&1)
echo "Python version: $python_version"

# Создаем виртуальное окружение
echo "Creating virtual environment..."
python3 -m venv venv

# Активируем виртуальное окружение
source venv/bin/activate

# Обновляем pip
echo "Upgrading pip..."
pip install --upgrade pip

# Устанавливаем зависимости
echo "Installing dependencies..."
pip install -r requirements.txt

# Создаем необходимые директории
mkdir -p logs
mkdir -p config

# Копируем .env в .env (если не существует)
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env .env
    echo "⚠️  Please update .env with your actual values!"
else
    echo ".env file already exists"
fi

# Инициализируем БД
echo "Initializing database..."
python setup_db.py

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Run: python main.py"
echo "3. For deposit listener: python transaction/raffle_processor.py"
echo "4. For event listener: python transaction/event_listener.py"
echo "5. For API server: python bot_api/api_handlers.py"
