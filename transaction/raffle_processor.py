import logging
import asyncio
import time
from datetime import datetime
from contracts.raffle_service import RaffleService
from database.db_service import UserService, TransactionService
from wallet.wallet_manager import WalletManager

logger = logging.getLogger(__name__)


class RaffleProcessor:
    def __init__(self):
        self.contract_manager = RaffleService()
        self.wallet_manager = WalletManager()
    
    def process_user_entry(self, tg_id: str, evm_address: str, encrypted_key: str) -> dict:
        """
        Обработать вход пользователя в лотерею
        
        Args:
            tg_id: Telegram ID пользователя
            evm_address: EVM адрес кошелька
            encrypted_key: Зашифрованный приватный ключ
        
        Returns:
            {
                'success': bool,
                'tx_hash': str,
                'error': str (если ошибка)
            }
        """
        try:
            logger.info(f"Processing entry for user {tg_id} ({evm_address})")
            
            private_key = self.wallet_manager.decrypt_private_key(encrypted_key)
            
            raffle_state = self.contract_manager.get_raffle_state()
            if raffle_state != 0:  # 0 = OPEN
                raise ValueError("Raffle is not open for entries")
            
            tx_hash = self.contract_manager.enter_raffle(evm_address, private_key)
            
            TransactionService.create_transaction(
                tg_id=tg_id,
                tx_hash=tx_hash,
                tx_type='ENTER_RAFFLE',
                from_addr=evm_address,
                to_addr=self.contract_manager.raffle_contract.address,
                amount=self.contract_manager.get_entrance_fee()
            )
            
            UserService.mark_in_raffle(tg_id)
            
            logger.info(f"Entry processed for {tg_id}. Tx: {tx_hash}")
            
            return {
                'success': True,
                'tx_hash': tx_hash,
                'error': None
            }
        
        except Exception as e:
            logger.error(f"Error processing entry for {tg_id}: {e}")
            return {
                'success': False,
                'tx_hash': None,
                'error': str(e)
            }
    
    def check_user_balance(self, evm_address: str) -> int:
        """Получить баланс USDT пользователя"""
        try:
            balance = self.contract_manager.get_usdt_balance(evm_address)
            return balance
        except Exception as e:
            logger.error(f"Error checking balance: {e}")
            return 0
    
    def get_raffle_status(self) -> dict:
        """Получить статус текущей лотереи"""
        try:
            players = self.contract_manager.get_players()
            raffle_state = self.contract_manager.get_raffle_state()
            entrance_fee = self.contract_manager.get_entrance_fee()
            
            states = {0: "OPEN", 1: "CALCULATING"}
            
            return {
                'players_count': len(players),
                'state': states.get(raffle_state, 'UNKNOWN'),
                'entrance_fee': entrance_fee,
                'pool': len(players) * entrance_fee
            }
        except Exception as e:
            logger.error(f"Error getting raffle status: {e}")
            return {}
    
    def trigger_raffle_draw(self) -> dict:
        """
        Запустить розыгрыш (вызывает performUpkeep)
        
        Returns:
            {
                'success': bool,
                'tx_hash': str,
                'vrf_request_id': str (если получен)
            }
        """
        try:
            logger.info("Triggering raffle draw...")
            
            tx_hash = self.contract_manager.perform_upkeep()
            
            logger.info(f"Draw triggered. Tx: {tx_hash}")
            
            return {
                'success': True,
                'tx_hash': tx_hash,
                'vrf_request_id': None
            }
        
        except Exception as e:
            logger.error(f"Error triggering draw: {e}")
            return {
                'success': False,
                'tx_hash': None,
                'vrf_request_id': None,
                'error': str(e)
            }


class DepositListener:
    """
    Слушает входящие платежи в USDT на адреса пользователей
    """
    def __init__(self):
        self.contract_manager = RaffleService()
        self.poll_interval = 10  # секунд
    
    async def listen_for_deposits(self, run_once=False):
        """
        Запустить слушателя входящих депозитов
        
        Args:
            run_once: Если True, проверит только один раз и выйдет
        """
        logger.info("Starting deposit listener...")
        
        while True:
            try:
                current_block = self.contract_manager.w3.eth.block_number
                last_checked_block = max(0, current_block - 10)

                logger.info(f"Checking for deposits. Block range: {last_checked_block} - {current_block}")
                
                transfer_logs = self.contract_manager.usdt_contract.events.Transfer.get_logs(
                    fromBlock=last_checked_block,
                    toBlock=current_block
                )
                
                for log in transfer_logs:
                    sender = log['args']['from']
                    recipient = log['args']['to']
                    amount = log['args']['value']
                    tx_hash = log['transactionHash'].hex()
                    
                    user = UserService.get_user_by_address(recipient)
                    
                    if user:
                        logger.info(f"Deposit detected for {user.tg_id}: {amount} wei (tx: {tx_hash})")
                        
                        UserService.update_user_deposit(user.tg_id, amount, tx_hash)
                        
                        TransactionService.create_transaction(
                            tg_id=user.tg_id,
                            tx_hash=tx_hash,
                            tx_type='DEPOSIT',
                            from_addr=sender,
                            to_addr=recipient,
                            amount=amount
                        )
                        
                        logger.info(f"Deposit recorded for {user.tg_id}")
                
                if run_once:
                    break
                
                await asyncio.sleep(self.poll_interval)
            
            except Exception as e:
                logger.error(f"Error in deposit listener: {e}")
                if run_once:
                    raise
                await asyncio.sleep(self.poll_interval)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    processor = RaffleProcessor()
    
    status = processor.get_raffle_status()
    print(f"Raffle status: {status}")
