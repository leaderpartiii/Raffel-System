import logging
import asyncio
from transaction.event_listener import EventListener
from transaction.raffle_processor import DepositListener
from bot_api.api_handlers import app
from config.settings import config

logging.basicConfig(
    level=config.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def consume_generator(gen, name="Listener"):
    """Вспомогательная функция для запуска генератора в фоне"""
    try:
        async for event in gen:
            logger.info(f"[{name}] Received event: {event}")
            # Тут можно добавить логику обработки события, если она нужна на уровне main
            # Например, отправку в очередь сообщений или вебхук
    except Exception as e:
        logger.error(f"[{name}] Error: {e}")

async def run_listeners():
    """Запустить все слушатели событий"""
    logger.info("Starting event listeners...")
    
    event_listener = EventListener()
    deposit_listener = DepositListener()
    
    # Запускаем слушатели параллельно
    tasks = [
        asyncio.create_task(consume_generator(event_listener.listen_for_winner())),
        asyncio.create_task(consume_generator(event_listener.listen_for_entries())),
        asyncio.create_task(deposit_listener.listen_for_deposits())
    ]
    
    try:
        await asyncio.gather(*tasks)
    except Exception as e:
        logger.error(f"Error in listeners: {e}")


def run_api_server():
    """Запустить API сервер"""
    logger.info(f"Starting API server on {config.API_HOST}:{config.API_PORT}")
    app.run(host=config.API_HOST, port=config.API_PORT)


if __name__ == "__main__":
    logger.info("🎰 Raffle Backend Starting...")
    logger.info(f"RPC URL: {config.RPC_URL}")
    logger.info(f"Contract Address: {config.RAFFLE_CONTRACT_ADDRESS}")
    
    # Выбор режима запуска
    import sys
    
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == "listeners":
            asyncio.run(run_listeners())
        elif mode == "api":
            run_api_server()
        else:
            print("Usage: python main.py [listeners|api]")
    else:
        # Запускаем оба в разных потоках (для локального тестирования)
        import threading
        
        listener_thread = threading.Thread(target=lambda: asyncio.run(run_listeners()))
        listener_thread.daemon = True
        listener_thread.start()
        
        run_api_server()
