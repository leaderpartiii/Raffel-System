# contracts/raffle_service.py

import logging
from web3 import Web3
from config.settings import config
from .blockchain_client import BlockchainClient

logger = logging.getLogger(__name__)

ERC20_ABI = [
    {"type": "function", "name": "approve",
     "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}],
     "outputs": [{"name": "", "type": "bool"}], "stateMutability": "nonpayable"},
    {"type": "function", "name": "balanceOf", "inputs": [{"name": "account", "type": "address"}],
     "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view"},
    {"type": "function", "name": "allowance",
     "inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}],
     "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view"},
    {"name": "Transfer", "type": "event",
     "inputs": [{"indexed": True, "name": "from", "type": "address"},
                {"indexed": True, "name": "to", "type": "address"},
                {"indexed": False, "name": "value", "type": "uint256"}
                ], "anonymous": False, }
]


class RaffleService:
    def __init__(self):
        self.client = BlockchainClient()
        self.w3 = self.client.w3
        self.raffle_contract = self.client.raffle_contract

        json_usdt_address = self.client.contract_data.get('usdt_address')

        if json_usdt_address:
            logger.info(f"Using USDT address from JSON: {json_usdt_address}")
            self.usdt_contract = self.client.get_contract_by_address(
                json_usdt_address,
                ERC20_ABI
            )
        elif config.USDT_CONTRACT_ADDRESS:
            self.usdt_contract = self.client.get_contract_by_address(
                config.USDT_CONTRACT_ADDRESS,
                ERC20_ABI
            )

        self.admin_address = Web3.to_checksum_address(config.ADMIN_PUBLIC_ADDRESS)
        self.admin_key = config.ADMIN_PRIVATE_KEY

    def get_entrance_fee(self) -> int:
        return self.raffle_contract.functions.s_depositAmount().call()

    def get_raffle_state(self) -> int:
        return self.raffle_contract.functions.s_raffleState().call()

    def enter_raffle(self, user_address: str, user_private_key: str) -> str:
        user_address = Web3.to_checksum_address(user_address)
        entrance_fee = self.get_entrance_fee()

        if hasattr(self, 'usdt_contract'):
            balance = self.usdt_contract.functions.balanceOf(user_address).call()
            if balance < entrance_fee:
                raise ValueError(f"Insufficient USDT balance. Have: {balance}, Need: {entrance_fee}")

            allowance = self.usdt_contract.functions.allowance(user_address, self.raffle_contract.address).call()

            if allowance < entrance_fee:
                logger.info("Approving USDT...")
                self._send_transaction(
                    self.usdt_contract.functions.approve(self.raffle_contract.address, entrance_fee),
                    user_address,
                    user_private_key
                )

        logger.info(f"Entering raffle for {user_address}...")
        tx_hash = self._send_transaction(
            self.raffle_contract.functions.deposit(),
            user_address,
            user_private_key,
        )
        return tx_hash

    def _send_transaction(self, function_call, from_address, private_key, value=0):
        nonce = self.w3.eth.get_transaction_count(from_address)

        tx_params = {
            'from': from_address,
            'nonce': nonce,
            'gasPrice': self.w3.eth.gas_price,
            'value': value,
            'chainId': self.w3.eth.chain_id
        }

        gas_estimate = function_call.estimate_gas(tx_params)
        tx_params['gas'] = int(gas_estimate * 1.2)

        transaction = function_call.build_transaction(tx_params)

        signed_tx = self.w3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)

        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status != 1:
            raise Exception(f"Transaction failed: {receipt}")

        return tx_hash.hex()


if __name__ == "__main__":
    service = RaffleService()
    print(f"Fee: {service.get_entrance_fee()}")
    print(f"State: {service.get_raffle_state()}")
