import logging
import asyncio
from contracts.contract_manager import RaffleContractManager
from database.db_service import UserService, RaffleService, TransactionService

logger = logging.getLogger(__name__)


class EventListener:
    """
    Слушает события смарт-контракта:
    - WinnerPicked: когда определен победитель
    - RaffleEnter: когда пользователь входит
    """
    def __init__(self):
        self.contract_manager = RaffleContractManager()
        self.poll_interval = 5  # секунд
    
    async def listen_for_winner(self, run_once=False):
        """
        Слушать событие WinnerPicked (победитель выбран)
        
        Args:
            run_once: Если True, проверит только один раз и выйдет
        """
        logger.info("Starting WinnerPicked listener...")
        
        last_checked_block = self.contract_manager.w3.eth.block_number - 100
        
        while True:
            try:
                current_block = self.contract_manager.w3.eth.block_number
                
                # Получаем логи события WinnerPicked
                winner_events = self.contract_manager.raffle_contract.events.WinnerPicked.get_logs(
                    from_block=last_checked_block,
                    to_block=current_block
                )
                
                for event in winner_events:
                    winner_address = event['args']['winner']
                    prize_amount = event['args']['prizeAmount']
                    tx_hash = event['transactionHash'].hex()
                    block_number = event['blockNumber']
                    
                    logger.info(f"🎉 WinnerPicked event detected!")
                    logger.info(f"Winner: {winner_address}")
                    logger.info(f"Prize: {prize_amount} wei")
                    logger.info(f"Tx: {tx_hash}")
                    
                    # Находим пользователя в БД
                    user = UserService.get_user_by_address(winner_address)
                    
                    if user:
                        logger.info(f"Winner found in DB: {user.tg_id}")
                        
                        # Обновляем статистику пользователя
                        UserService.get_session().query(UserService.User).filter(
                            UserService.User.evm_address == winner_address
                        ).update({
                            UserService.User.total_winnings: UserService.User.total_winnings + prize_amount,
                            UserService.User.is_in_current_raffle: False
                        })
                        
                        # Создаем запись о выигрыше
                        TransactionService.create_transaction(
                            tg_id=user.tg_id,
                            tx_hash=tx_hash,
                            tx_type='WIN_PRIZE',
                            from_addr=self.contract_manager.raffle_contract.address,
                            to_addr=winner_address,
                            amount=prize_amount
                        )
                        
                        # Отмечаем транзакцию как подтвержденную
                        TransactionService.mark_transaction_confirmed(tx_hash, block_number=block_number)
                        
                        # ВАЖНО: Бот должен получить это уведомление (интеграция с Роль 2)
                        yield {
                            'type': 'WINNER_PICKED',
                            'winner_tg_id': user.tg_id,
                            'winner_address': winner_address,
                            'prize_amount': prize_amount,
                            'tx_hash': tx_hash
                        }
                    else:
                        logger.warning(f"Winner not found in DB: {winner_address}")
                
                last_checked_block = current_block
                
                if run_once:
                    break
                
                await asyncio.sleep(self.poll_interval)
            
            except Exception as e:
                logger.error(f"Error in winner listener: {e}")
                if run_once:
                    raise
                await asyncio.sleep(self.poll_interval)
    
    async def listen_for_entries(self, run_once=False):
        """
        Слушать событие RaffleEnter (пользователь входит в лотерею)
        
        Args:
            run_once: Если True, проверит только один раз и выйдет
        """
        logger.info("Starting RaffleEnter listener...")
        
        last_checked_block = self.contract_manager.w3.eth.block_number - 100
        
        while True:
            try:
                current_block = self.contract_manager.w3.eth.block_number
                
                # Получаем логи события RaffleEnter
                entry_events = self.contract_manager.raffle_contract.events.RaffleEnter.get_logs(
                    from_block=last_checked_block,
                    to_block=current_block
                )
                
                for event in entry_events:
                    player_address = event['args']['player']
                    tx_hash = event['transactionHash'].hex()
                    block_number = event['blockNumber']
                    
                    logger.info(f"RaffleEnter event: {player_address} (tx: {tx_hash})")
                    
                    # Находим пользователя
                    user = UserService.get_user_by_address(player_address)
                    if user:
                        # Отмечаем транзакцию как подтвержденную
                        TransactionService.mark_transaction_confirmed(tx_hash, block_number=block_number)
                        
                        logger.info(f"Entry confirmed for {user.tg_id}")
                        
                        yield {
                            'type': 'RAFFLE_ENTER',
                            'tg_id': user.tg_id,
                            'player_address': player_address,
                            'tx_hash': tx_hash
                        }
                
                last_checked_block = current_block
                
                if run_once:
                    break
                
                await asyncio.sleep(self.poll_interval)
            
            except Exception as e:
                logger.error(f"Error in entry listener: {e}")
                if run_once:
                    raise
                await asyncio.sleep(self.poll_interval)


async def run_event_listener():
    """
    Основной loop, который слушает ВСЕ события
    (интеграция с Роль 4 - Event Listener & DevOps)
    """
    listener = EventListener()
    
    # Создаем корутины для обоих слушателей
    winner_task = asyncio.create_task(listener.listen_for_winner())
    entry_task = asyncio.create_task(listener.listen_for_entries())
    
    # Обработка результатов
    async for notification in winner_task:
        logger.info(f"Notification: {notification}")
        # Здесь отправляем уведомление боту (через API)
    
    await asyncio.gather(winner_task, entry_task)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_event_listener())
