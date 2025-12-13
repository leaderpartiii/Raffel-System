import logging
import asyncio
from contracts.raffle_service import RaffleService
from database.db_service import UserService, TransactionService

from backend.main import consume_generator

logger = logging.getLogger(__name__)


class EventListener:
    def __init__(self):
        self.contract_manager = RaffleService()
        self.poll_interval = 5  # секунд
    
    async def listen_for_winner(self, run_once=False):
        """
        Слушать событие WinnerPicked (победитель выбран)
        
        Args:
            run_once: Если True, проверит только один раз и выйдет
        """
        logger.info("Starting WinnerPicked listener...")
        

        while True:
            try:
                current_block = self.contract_manager.w3.eth.block_number
                last_checked_block = max(current_block - 100, 0)

                winner_events = self.contract_manager.raffle_contract.events.WinnerSelected.get_logs(
                    fromBlock=last_checked_block,
                    toBlock=current_block
                )
                
                for event in winner_events:
                    winner_address = event['args']['winner']
                    prize_amount = event['args']['winningAmount']
                    tx_hash = event['transactionHash'].hex()
                    block_number = event['blockNumber']
                    
                    logger.info(f"🎉 WinnerSelected event detected!")
                    logger.info(f"Winner: {winner_address}")
                    logger.info(f"Prize: {prize_amount} wei")
                    logger.info(f"Tx: {tx_hash}")
                    
                    user = UserService.get_user_by_address(winner_address)
                    
                    if user:
                        logger.info(f"Winner found in DB: {user.tg_id}")
                        
                        UserService.get_session().query(UserService.User).filter(
                            UserService.User.evm_address == winner_address
                        ).update({
                            UserService.User.total_winnings: UserService.User.total_winnings + prize_amount,
                            UserService.User.is_in_current_raffle: False
                        })
                        
                        TransactionService.create_transaction(
                            tg_id=user.tg_id,
                            tx_hash=tx_hash,
                            tx_type='WIN_PRIZE',
                            from_addr=self.contract_manager.raffle_contract.address,
                            to_addr=winner_address,
                            amount=prize_amount
                        )
                        
                        TransactionService.mark_transaction_confirmed(tx_hash, block_number=block_number)
                        
                        yield {
                            'type': 'WINNER_PICKED',
                            'winner_tg_id': user.tg_id,
                            'winner_address': winner_address,
                            'prize_amount': prize_amount,
                            'tx_hash': tx_hash
                        }
                    else:
                        logger.warning(f"Winner not found in DB: {winner_address}")
                

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
        

        while True:
            try:

                current_block = self.contract_manager.w3.eth.block_number
                last_checked_block = max(current_block - 100, 0)

                entry_events = self.contract_manager.raffle_contract.events.Deposited.get_logs(
                    fromBlock=last_checked_block,
                    toBlock=current_block
                )
                
                for event in entry_events:
                    player_address = event['args']['participant']
                    tx_hash = event['transactionHash'].hex()
                    block_number = event['blockNumber']
                    
                    logger.info(f"RaffleEnter event: {player_address} (tx: {tx_hash})")
                    
                    user = UserService.get_user_by_address(player_address)
                    if user:
                        TransactionService.mark_transaction_confirmed(tx_hash, block_number=block_number)
                        
                        logger.info(f"Entry confirmed for {user.tg_id}")
                        
                        yield {
                            'type': 'RAFFLE_ENTER',
                            'tg_id': user.tg_id,
                            'player_address': player_address,
                            'tx_hash': tx_hash
                        }
                
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
    
    winner_task = asyncio.create_task(consume_generator(listener.listen_for_winner()))
    entry_task = asyncio.create_task(consume_generator(listener.listen_for_entries()))
    
    async for notification in winner_task:
        logger.info(f"Notification: {notification}")

    await asyncio.gather(winner_task, entry_task)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_event_listener())
