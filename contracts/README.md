# 🎰 Raffle Backend - Роль 3 (Backend Logic & Wallet Manager)

Это полный backend для работы с лотереей Raffle Smart Contract. Модуль отвечает за управление кошельками, обработку депозитов, отправку транзакций в блокчейн и слушание событий.

## 📋 Структура проекта

```
raffle_backend/
├── config/
│   └── settings.py              # Конфигурация (RPC, адреса контрактов)
├── contracts/
│   └── contract_manager.py      # Работа со смарт-контрактом через Web3
├── wallet/
│   └── wallet_manager.py        # Генерация кошельков и шифрование ключей
├── database/
│   ├── models.py                # SQLAlchemy модели (User, Raffle, Transaction)
│   └── db_service.py            # CRUD сервисы для БД
├── transaction/
│   ├── raffle_processor.py      # Обработка входов и мониторинг депозитов
│   └── event_listener.py        # Слушатель событий смарт-контракта
├── bot_api/
│   └── api_handlers.py          # Flask API для интеграции с ботом
├── main.py                      # Точка входа
├── setup_db.py                  # Инициализация БД
├── requirements.txt             # Зависимости
├── .env.example                 # Шаблон конфигурации
├── setup.sh                     # Setup скрипт (Linux/Mac)
└── setup.bat                    # Setup скрипт (Windows)
```

## 🚀 Быстрый старт

### 1️⃣ Система требования
- **Python 3.9+**
- **pip** (идёт с Python)
- **Git** (опционально)

### 2️⃣ Клонируем репозиторий (если нужно)
```bash
git clone https://github.com/yourusername/raffle-backend.git
cd raffle-backend
```

### 3️⃣ Создаем и активируем виртуальное окружение

#### На Linux / MacOS:
```bash
# Создаем виртуальное окружение
python3 -m venv venv

# Активируем его
source venv/bin/activate

# Должно было вывести: (venv) в начало строки терминала
```

#### На Windows:
```bash
# Создаем виртуальное окружение
python -m venv venv

# Активируем его
venv\Scripts\activate.bat

# Должно было вывести: (venv) в начало строки PowerShell/CMD
```

### 4️⃣ Устанавливаем зависимости

```bash
# Убедитесь, что venv активирован!
pip install --upgrade pip
pip install -r requirements.txt
```

Это займет ~2 минуты. Должны установиться:
- `web3.py` - для работы с блокчейном
- `sqlalchemy` - для БД
- `python-dotenv` - для конфигурации
- `cryptography` - для шифрования
- `flask` - для API сервера

### 5️⃣ Конфигурируем приложение

#### Шаг 1: Копируем .env.example в .env
```bash
cp .env.example .env
```

#### Шаг 2: Редактируем .env
Откройте файл `.env` и заполните следующие значения:

```env
# Blockchain RPC (пример для Sepolia)
RPC_URL=https://sepolia.infura.io/v3/YOUR_INFURA_KEY
CHAIN_ID=11155111

# Адреса контрактов (получите из смарт-контракта)
RAFFLE_CONTRACT_ADDRESS=0x1234...
USDT_CONTRACT_ADDRESS=0x5678...

# Кошелек админа (для запуска розыгрыша)
ADMIN_PRIVATE_KEY=0x1234...
ADMIN_PUBLIC_ADDRESS=0x5678...

# Шифрование (используйте строку ровно 32 символа!)
ENCRYPTION_KEY=your_secret_key_32_chars_long!!!

# API
API_HOST=0.0.0.0
API_PORT=8000
```

**⚠️ ВАЖНО:**
- Никогда не коммитьте `.env` файл в Git!
- Храните приватные ключи в безопасности
- Для продакшена используйте переменные окружения вместо .env файла

### 6️⃣ Инициализируем БД

```bash
python setup_db.py
```

Должно создаться три таблицы:
- `users` - пользователи с кошельками
- `raffles` - истории лотерей
- `transactions` - все транзакции

## 🏃 Запуск приложения

### Вариант 1: Запустить всё сразу (для разработки)
```bash
python main.py
```

Это запустит:
- API сервер на `http://localhost:8000`
- Слушатели событий в фоновом потоке

### Вариант 2: Запустить отдельно (для продакшена)

**Терминал 1 - API сервер:**
```bash
python main.py api
```

**Терминал 2 - Слушатели событий:**
```bash
python main.py listeners
```

**Терминал 3 - Только депозиты (опционально):**
```bash
python -c "from transaction.raffle_processor import DepositListener; import asyncio; asyncio.run(DepositListener().listen_for_deposits())"
```

## 🔌 API Endpoints (для Роль 2 - Telegram Bot)

### 1. Генерация кошелька
```bash
curl -X POST http://localhost:8000/api/wallet/generate \
  -H "Content-Type: application/json" \
  -d '{"tg_id": "123456789"}'

# Ответ:
{
  "success": true,
  "address": "0x...",
  "private_key": "0x...",
  "message": "Wallet generated. Keep private key safe!"
}
```

### 2. Получить баланс USDT
```bash
curl http://localhost:8000/api/wallet/balance/123456789

# Ответ:
{
  "success": true,
  "balance": 1000000000000000000,
  "balance_usdt": 1.0
}
```

### 3. Статус лотереи
```bash
curl http://localhost:8000/api/raffle/status

# Ответ:
{
  "success": true,
  "players_count": 5,
  "state": "OPEN",
  "entrance_fee": 1000000000000000000,
  "pool": 5000000000000000000
}
```

### 4. Вход в лотерею
```bash
curl -X POST http://localhost:8000/api/raffle/enter \
  -H "Content-Type: application/json" \
  -d '{"tg_id": "123456789"}'

# Ответ:
{
  "success": true,
  "tx_hash": "0x...",
  "message": "Entry processed"
}
```

### 5. Запустить розыгрыш (ТОЛЬКО АДМИН)
```bash
curl -X POST http://localhost:8000/api/raffle/draw \
  -H "Authorization: Bearer YOUR_SECRET_KEY"

# Ответ:
{
  "success": true,
  "tx_hash": "0x..."
}
```

### 6. Статистика пользователя
```bash
curl http://localhost:8000/api/user/stats/123456789

# Ответ:
{
  "success": true,
  "total_entries": 3,
  "total_winnings": 5000000000000000000,
  "current_deposit": 1000000000000000000,
  "is_in_raffle": true
}
```

## 📊 Структура данных в БД

### Таблица users
```sql
id (PK)
tg_id (уникален)          -- Telegram ID пользователя
evm_address (уникален)    -- Адрес кошелька (0x...)
encrypted_private_key     -- Зашифрованный приватный ключ
is_in_current_raffle      -- Участвует ли в текущей лотерее
deposit_amount            -- Сумма депозита в wei
deposit_tx_hash           -- Хеш транзакции депозита
total_entries             -- Всего участий
total_winnings            -- Всего выигрышей
created_at
updated_at
```

### Таблица raffles
```sql
id (PK)
raffle_id (уникален)      -- ID лотереи
status                    -- OPEN, CALCULATING, CLOSED
total_participants        -- Количество участников
total_pool                -- Общий призовой фонд
winner_address            -- Адрес победителя
prize_amount              -- Размер приза
vrf_request_id            -- ID запроса Chainlink VRF
started_at
ended_at
```

### Таблица transactions
```sql
id (PK)
tg_id
tx_hash (уникален)        -- Хеш транзакции
tx_type                   -- DEPOSIT, ENTER_RAFFLE, WIN_PRIZE
from_address
to_address
amount
status                    -- PENDING, CONFIRMED, FAILED
gas_used
block_number
created_at
confirmed_at
```

## 🔒 Безопасность

### Управление приватными ключами
1. **Генерация**: `WalletManager.generate_wallet()` создает новый кошелек
2. **Хранение**: Приватный ключ сразу шифруется с помощью `Fernet` (из cryptography)
3. **Использование**: При отправке транзакции ключ расшифровывается, используется, потом удаляется из памяти

```python
# Пример использования
wallet_manager = WalletManager()
wallet = wallet_manager.generate_wallet()

# wallet['private_key'] - для отправки пользователю (ОДИН РАЗ!)
# wallet['encrypted_private_key'] - для хранения в БД
```

### Шифрование
- **Алгоритм**: AES (через Fernet)
- **Размер ключа**: 32 байта (256 бит)
- **Ключ**: Из переменной `ENCRYPTION_KEY` в .env

### ⚠️ ВНИМАНИЕ для продакшена
Текущая реализация использует **кастодиальные кошельки** (приватные ключи хранятся на сервере). Это опасно!

**Лучше:**
1. Использовать **MPC (Multi-Party Computation)** сервисы (Fireblocks, Coinbase Cloud)
2. Использовать **Account Abstraction** (ERC-4337)
3. Просить пользователей подписывать транзакции через MetaMask

## 📝 Логирование

Логи пишутся в:
- **Console** (stdout)
- **Файл** `logs/raffle.log`

Уровень логирования настраивается в `.env`:
```env
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

## 🧪 Тестирование локально

### Без подключения к блокчейну (мокирование)
```python
from contracts.contract_manager import RaffleContractManager
from wallet.wallet_manager import WalletManager

# Генерируем кошелек
wallet_manager = WalletManager()
wallet = wallet_manager.generate_wallet()
print(f"Address: {wallet['address']}")

# Шифруем/расшифровываем
encrypted = wallet_manager.encrypt_private_key(wallet['private_key'])
decrypted = wallet_manager.decrypt_private_key(encrypted)
print(f"Keys match: {decrypted == wallet['private_key']}")
```

### С реальной сетью (Sepolia)
1. Получите тестовые токены USDT на Sepolia
2. Отправьте себе ETH для газа
3. Обновите `.env` с реальными адресами
4. Запустите приложение и протестируйте API

## 🐛 Troubleshooting

### Ошибка: "Failed to connect to RPC"
```
Проверьте:
1. RPC_URL в .env правильный
2. Интернет соединение
3. RPC сервис доступен
```

### Ошибка: "Contract address is not a valid Ethereum address"
```
Проверьте:
1. RAFFLE_CONTRACT_ADDRESS и USDT_CONTRACT_ADDRESS в .env
2. Адреса начинаются с "0x"?
3. Адреса для той же сети, что и RPC_URL?
```

### Ошибка при шифровании: "Encryption key must be exactly 32 characters long"
```
Проверьте ENCRYPTION_KEY в .env - должна быть ровно 32 символа
```

### БД зарегистрирована, но таблицы не созданы
```bash
# Пересоздайте БД
rm raffle.db
python setup_db.py
```

## 📚 Документация компонентов

### ContractManager
Управляет взаимодействием со смарт-контрактом:
- `get_entrance_fee()` - стоимость входа
- `get_players()` - список участников
- `enter_raffle(address, key)` - вход в лотерею
- `perform_upkeep()` - запуск розыгрыша
- `get_event_logs(event_name)` - логи событий

### WalletManager
Управляет кошельками:
- `generate_wallet()` - создать новый кошелек
- `encrypt_private_key(key)` - зашифровать ключ
- `decrypt_private_key(encrypted)` - расшифровать ключ

### RaffleProcessor
Обработка логики:
- `process_user_entry()` - пользователь входит
- `check_user_balance()` - проверить баланс
- `trigger_raffle_draw()` - запустить розыгрыш
- `get_raffle_status()` - статус лотереи

### EventListener & DepositListener
Слушатели событий:
- Мониторят блокчейн в реальном времени
- Обновляют БД при новых событиях
- Отправляют уведомления боту

## 🔗 Интеграция с Ролью 2 (Telegram Bot)

Бот вызывает этот backend через HTTP API:

```
Бот запрашивает       Backend обрабатывает    Блокчейн
POST /wallet/generate --> WalletManager        --> генерирует кошелек
POST /raffle/enter    --> RaffleProcessor      --> вызывает enterRaffle()
GET /raffle/status    --> ContractManager      --> читает состояние
(событие победителя)  <-- EventListener        <-- слушает WinnerPicked
```

## 🚢 Деплой на сервер

### Docker (рекомендуется)
```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "main.py"]
```

### Systemd (Linux)
```ini
[Unit]
Description=Raffle Backend
After=network.target

[Service]
Type=simple
User=raffle
WorkingDirectory=/home/raffle/raffle-backend
ExecStart=/home/raffle/raffle-backend/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## 📞 Поддержка

Вопросы? Создавайте Issue на GitHub или обратитесь к Роли 1 (System Architect)!

---

**Версия:** 1.0  
**Дата:** December 2025  
**Разработано для:** 🎰 Raffle Lottery System
