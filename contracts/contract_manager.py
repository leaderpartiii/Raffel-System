import json
import logging
from web3 import Web3
from config.settings import config

logger = logging.getLogger(__name__)

RAFFLE_ABI = [
    {
        "type": "function",
        "name": "enterRaffle",
        "inputs": [],
        "outputs": [],
        "stateMutability": "nonpayable"
    },
    {
        "type": "function",
        "name": "performUpkeep",
        "inputs": [{"name": "performData", "type": "bytes"}],
        "outputs": [],
        "stateMutability": "nonpayable"
    },
    {
        "type": "function",
        "name": "getPlayers",
        "inputs": [],
        "outputs": [{"name": "", "type": "address[]"}],
        "stateMutability": "view"
    },
    {
        "type": "function",
        "name": "getRaffleState",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint8"}],
        "stateMutability": "view"
    },
    {
        "type": "function",
        "name": "getEntranceFee",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view"
    },
    {
        "type": "function",
        "name": "getRecentWinner",
        "inputs": [],
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view"
    },
    {
        "type": "event",
        "name": "RaffleEnter",
        "inputs": [{"name": "player", "type": "address", "indexed": True}]
    },
    {
        "type": "event",
        "name": "RequestedRaffleWinner",
        "inputs": [{"name": "requestId", "type": "uint256", "indexed": True}]
    },
    {
        "type": "event",
        "name": "WinnerPicked",
        "inputs": [
            {"name": "winner", "type": "address", "indexed": True},
            {"name": "prizeAmount", "type": "uint256", "indexed": False}
        ]
    }
]

USDT_ABI = [
    {
        "type": "function",
        "name": "approve",
        "inputs": [
            {"name": "spender", "type": "address"},
            {"name": "amount", "type": "uint256"}
        ],
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "nonpayable"
    },
    {
        "type": "function",
        "name": "balanceOf",
        "inputs": [{"name": "account", "type": "address"}],
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view"
    },
    {
        "type": "function",
        "name": "transfer",
        "inputs": [
            {"name": "recipient", "type": "address"},
            {"name": "amount", "type": "uint256"}
        ],
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "nonpayable"
    },
    {
        "type": "function",
        "name": "allowance",
        "inputs": [
            {"name": "owner", "type": "address"},
            {"name": "spender", "type": "address"}
        ],
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view"
    },
    {
        "type": "event",
        "name": "Transfer",
        "inputs": [
            {"name": "from", "type": "address", "indexed": True},
            {"name": "to", "type": "address", "indexed": True},
            {"name": "value", "type": "uint256", "indexed": False}
        ]
    }
]


class RaffleContractManager:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(config.RPC_URL))
        if not self.w3.is_connected():
            raise ConnectionError(f"Failed to connect to RPC: {config.RPC_URL}")
        
        self.raffle_contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(config.RAFFLE_CONTRACT_ADDRESS),
            abi=RAFFLE_ABI
        )
        
        self.usdt_contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(config.USDT_CONTRACT_ADDRESS),
            abi=USDT_ABI
        )
        
        self.admin_address = Web3.to_checksum_address(config.ADMIN_PUBLIC_ADDRESS)
        self.admin_key = config.ADMIN_PRIVATE_KEY
        
        logger.info(f"RaffleContractManager initialized. Contract: {config.RAFFLE_CONTRACT_ADDRESS}")
    
    def get_entrance_fee(self) -> int:
        """Получить стоимость входа в лотерею (в wei)"""
        try:
            fee = self.raffle_contract.functions.getEntranceFee().call()
            logger.info(f"Entrance fee: {fee} wei")
            return fee
        except Exception as e:
            logger.error(f"Error getting entrance fee: {e}")
            raise
    
    def get_players(self) -> list:
        """Получить список всех участников"""
        try:
            players = self.raffle_contract.functions.getPlayers().call()
            logger.info(f"Current players: {len(players)}")
            return players
        except Exception as e:
            logger.error(f"Error getting players: {e}")
            raise
    
    def get_raffle_state(self) -> int:
        """Получить состояние лотереи (0=OPEN, 1=CALCULATING)"""
        try:
            state = self.raffle_contract.functions.getRaffleState().call()
            states = {0: "OPEN", 1: "CALCULATING"}
            logger.info(f"Raffle state: {states.get(state, 'UNKNOWN')}")
            return state
        except Exception as e:
            logger.error(f"Error getting raffle state: {e}")
            raise
    
    def get_recent_winner(self) -> str:
        """Получить адрес последнего победителя"""
        try:
            winner = self.raffle_contract.functions.getRecentWinner().call()
            logger.info(f"Recent winner: {winner}")
            return winner
        except Exception as e:
            logger.error(f"Error getting recent winner: {e}")
            raise
    
    def get_usdt_balance(self, address: str) -> int:
        """Получить баланс USDT адреса (в wei)"""
        try:
            address = Web3.to_checksum_address(address)
            balance = self.usdt_contract.functions.balanceOf(address).call()
            logger.info(f"USDT balance of {address}: {balance}")
            return balance
        except Exception as e:
            logger.error(f"Error getting USDT balance: {e}")
            raise
    
    def enter_raffle(self, user_address: str, user_private_key: str) -> str:
        """
        Участвовать в лотерее
        
        Args:
            user_address: адрес пользователя
            user_private_key: приватный ключ пользователя
        
        Returns:
            transaction hash
        """
        try:
            user_address = Web3.to_checksum_address(user_address)
            
            # 1. Проверяем баланс
            balance = self.get_usdt_balance(user_address)
            entrance_fee = self.get_entrance_fee()
            
            if balance < entrance_fee:
                raise ValueError(f"Insufficient USDT balance. Have: {balance}, Need: {entrance_fee}")
            
            # 2. Одобряем трату токенов контрактом
            nonce = self.w3.eth.get_transaction_count(user_address)
            
            approve_tx = self.usdt_contract.functions.approve(
                self.raffle_contract.address,
                entrance_fee
            ).build_transaction({
                'from': user_address,
                'nonce': nonce,
                'gas': 100000,
                'gasPrice': self.w3.eth.gas_price,
                'chainId': config.CHAIN_ID
            })
            
            signed_approve = self.w3.eth.account.sign_transaction(approve_tx, user_private_key)
            approve_hash = self.w3.eth.send_raw_transaction(signed_approve.rawTransaction)
            logger.info(f"Approve tx sent: {approve_hash.hex()}")
            
            # 3. Вызываем enterRaffle()
            nonce = self.w3.eth.get_transaction_count(user_address)
            
            enter_tx = self.raffle_contract.functions.enterRaffle().build_transaction({
                'from': user_address,
                'nonce': nonce,
                'gas': 200000,
                'gasPrice': self.w3.eth.gas_price,
                'chainId': config.CHAIN_ID
            })
            
            signed_enter = self.w3.eth.account.sign_transaction(enter_tx, user_private_key)
            enter_hash = self.w3.eth.send_raw_transaction(signed_enter.rawTransaction)
            logger.info(f"Enter raffle tx sent: {enter_hash.hex()}")
            
            return enter_hash.hex()
        
        except Exception as e:
            logger.error(f"Error entering raffle: {e}")
            raise
    
    def perform_upkeep(self) -> str:
        """Запустить розыгрыш (вызывается админом)"""
        try:
            nonce = self.w3.eth.get_transaction_count(self.admin_address)
            
            upkeep_tx = self.raffle_contract.functions.performUpkeep(b"").build_transaction({
                'from': self.admin_address,
                'nonce': nonce,
                'gas': 300000,
                'gasPrice': self.w3.eth.gas_price,
                'chainId': config.CHAIN_ID
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(upkeep_tx, self.admin_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            logger.info(f"Perform upkeep tx sent: {tx_hash.hex()}")
            
            return tx_hash.hex()
        
        except Exception as e:
            logger.error(f"Error performing upkeep: {e}")
            raise
    
    def wait_for_transaction(self, tx_hash: str, timeout: int = 120) -> dict:
        """Ожидать подтверждения транзакции"""
        try:
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
            logger.info(f"Transaction confirmed: {tx_hash}")
            return receipt
        except Exception as e:
            logger.error(f"Error waiting for transaction: {e}")
            raise
    
    def get_event_logs(self, event_name: str, from_block: int = 'latest') -> list:
        """Получить логи события"""
        try:
            if event_name == 'WinnerPicked':
                event = self.raffle_contract.events.WinnerPicked
            elif event_name == 'RaffleEnter':
                event = self.raffle_contract.events.RaffleEnter
            else:
                raise ValueError(f"Unknown event: {event_name}")
            
            logs = event.get_logs(from_block=from_block)
            logger.info(f"Found {len(logs)} {event_name} events")
            return logs
        
        except Exception as e:
            logger.error(f"Error getting event logs: {e}")
            raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    manager = RaffleContractManager()
    print(f"Entrance fee: {manager.get_entrance_fee()}")
    print(f"Players: {manager.get_players()}")
    print(f"Raffle state: {manager.get_raffle_state()}")
